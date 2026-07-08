from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tickets import services
from apps.tickets.metrics import dashboard_metrics
from apps.tickets.models import Notification
from apps.tickets.permissions import (
    DemoModeDeleteGuard,
    IsStaff,
    is_dispatcher,
    is_manager,
    is_staff_member,
)
from apps.tickets.serializers import (
    AssignSerializer,
    CommentCreateSerializer,
    NotificationSerializer,
    RequestCreateSerializer,
    RequestDetailSerializer,
    RequestListSerializer,
    TechnicianSerializer,
    WorkLogSerializer,
)

User = get_user_model()


def _forbidden(message="You cannot perform this action."):
    return Response({"detail": message}, status=status.HTTP_403_FORBIDDEN)


class RequestViewSet(viewsets.ModelViewSet):
    """Maintenance requests, scoped by role. Lifecycle transitions are actions."""

    permission_classes = [permissions.IsAuthenticated, DemoModeDeleteGuard]
    lookup_field = "reference"
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "priority", "department"]
    search_fields = ["reference", "title", "description"]
    ordering_fields = ["created_at", "sla_due_at", "priority", "status"]

    def get_queryset(self):
        from apps.tickets.permissions import visible_requests

        qs = visible_requests(self.request.user)
        if self.request.query_params.get("unassigned") == "true":
            qs = qs.filter(assignee__isnull=True)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return RequestCreateSerializer
        if self.action in ("retrieve", "update", "partial_update"):
            return RequestDetailSerializer
        return RequestListSerializer

    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        detail = RequestDetailSerializer(serializer.instance, context={"request": request})
        return Response(detail.data, status=status.HTTP_201_CREATED)

    def _detail_response(self, obj):
        obj.refresh_from_db()
        return Response(RequestDetailSerializer(obj, context={"request": self.request}).data)

    # --- lifecycle actions -------------------------------------------------

    @action(detail=True, methods=["post"])
    def receive(self, request, reference=None):
        obj = self.get_object()
        if not is_dispatcher(request.user):
            return _forbidden("Only a dispatcher can receive a request.")
        obj.receive(actor=request.user)
        return self._detail_response(obj)

    @action(detail=True, methods=["post"])
    def assign(self, request, reference=None):
        obj = self.get_object()
        if not is_dispatcher(request.user):
            return _forbidden("Only a dispatcher can assign a request.")
        ser = AssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        technician = User.objects.filter(pk=ser.validated_data["technician"]).first()
        if technician is None:
            return Response({"technician": "Unknown user."}, status=400)
        try:
            services.assign_request(obj, technician, actor=request.user)
        except ValidationError as exc:
            return Response({"detail": "; ".join(exc.messages)}, status=400)
        return self._detail_response(obj)

    @action(detail=True, methods=["post"])
    def reassign(self, request, reference=None):
        # Same operation as assign, allowed on an already-assigned request.
        return self.assign(request, reference)

    @action(detail=True, methods=["post"])
    def start(self, request, reference=None):
        obj = self.get_object()
        if not (obj.assignee_id == request.user.id or is_manager(request.user)):
            return _forbidden("Only the assigned technician can start work.")
        obj.start(actor=request.user)
        return self._detail_response(obj)

    @action(detail=True, methods=["post"])
    def hold(self, request, reference=None):
        obj = self.get_object()
        if not (obj.assignee_id == request.user.id or is_dispatcher(request.user)):
            return _forbidden()
        obj.hold(actor=request.user)
        return self._detail_response(obj)

    @action(detail=True, methods=["post"])
    def resume(self, request, reference=None):
        obj = self.get_object()
        if not (obj.assignee_id == request.user.id or is_dispatcher(request.user)):
            return _forbidden()
        obj.resume(actor=request.user)
        return self._detail_response(obj)

    @action(detail=True, methods=["post"])
    def complete(self, request, reference=None):
        obj = self.get_object()
        if not (obj.assignee_id == request.user.id or is_manager(request.user)):
            return _forbidden("Only the assigned technician can complete work.")
        obj.mark_completed(actor=request.user)
        return self._detail_response(obj)

    @action(detail=True, methods=["post"])
    def close(self, request, reference=None):
        obj = self.get_object()
        if not (obj.requester_id == request.user.id or is_dispatcher(request.user)):
            return _forbidden()
        obj.mark_closed(actor=request.user)
        return self._detail_response(obj)

    @action(detail=True, methods=["post"])
    def cancel(self, request, reference=None):
        obj = self.get_object()
        if not (obj.requester_id == request.user.id or is_dispatcher(request.user)):
            return _forbidden()
        obj.cancel(actor=request.user)
        return self._detail_response(obj)

    @action(detail=True, methods=["post"])
    def reopen(self, request, reference=None):
        obj = self.get_object()
        if not (obj.requester_id == request.user.id or is_dispatcher(request.user)):
            return _forbidden()
        obj.reopen(actor=request.user)
        return self._detail_response(obj)

    @action(detail=True, methods=["get"], url_path="eligible-technicians")
    def eligible_technicians(self, request, reference=None):
        obj = self.get_object()
        if not is_dispatcher(request.user):
            return _forbidden()
        techs = services.eligible_technicians(obj.department)
        return Response(TechnicianSerializer(techs, many=True).data)

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, reference=None):
        obj = self.get_object()
        if request.method == "GET":
            qs = obj.worklogs.select_related("author").all()
            if not is_staff_member(request.user):
                qs = qs.filter(is_internal=False)
            return Response(WorkLogSerializer(qs, many=True).data)
        ser = CommentCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        is_internal = ser.validated_data.get("is_internal", False) and is_staff_member(
            request.user
        )
        obj.worklogs.create(
            author=request.user, body=ser.validated_data["body"], is_internal=is_internal
        )
        worklogs = obj.worklogs.select_related("author")
        return Response(WorkLogSerializer(worklogs, many=True).data, status=201)


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    pagination_class = None

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)[:50]

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread": count})

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        Notification.objects.filter(user=request.user, pk=pk).update(is_read=True)
        return Response({"status": "ok"})

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"status": "ok"})


class MetricsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsStaff]

    def get(self, request):
        return Response(dashboard_metrics(request.user))
