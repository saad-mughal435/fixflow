from rest_framework import serializers

from apps.catalog.serializers import DepartmentSerializer
from apps.tickets.models import Notification, Request, RequestEvent, WorkLog
from apps.tickets.permissions import is_staff_member


class MiniUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.get_full_name() or obj.get_username()


class TechnicianSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    name = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.get_full_name() or obj.get_username()

    def get_title(self, obj):
        profile = getattr(obj, "staff_profile", None)
        return profile.title if profile else ""


class RequestEventSerializer(serializers.ModelSerializer):
    verb_display = serializers.CharField(source="get_verb_display", read_only=True)
    actor = serializers.CharField(source="actor.username", read_only=True, default=None)

    class Meta:
        model = RequestEvent
        fields = ["id", "verb", "verb_display", "actor", "from_value", "to_value", "created_at"]


class WorkLogSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = WorkLog
        fields = ["id", "author_name", "body", "is_internal", "created_at"]

    def get_author_name(self, obj):
        if not obj.author:
            return "system"
        return obj.author.get_full_name() or obj.author.get_username()


class RequestListSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    requester = MiniUserSerializer(read_only=True)
    assignee = MiniUserSerializer(read_only=True)
    location_label = serializers.CharField(source="location.label", read_only=True, default=None)
    community = serializers.CharField(source="location.community", read_only=True, default=None)
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = Request
        fields = [
            "id", "reference", "title", "status", "status_display", "priority",
            "priority_display", "department", "category_name", "location_label",
            "community", "requester", "assignee", "sla_due_at", "sla_breached",
            "is_open", "created_at", "updated_at",
        ]


class RequestDetailSerializer(RequestListSerializer):
    events = RequestEventSerializer(many=True, read_only=True)
    worklogs = serializers.SerializerMethodField()

    class Meta(RequestListSerializer.Meta):
        fields = RequestListSerializer.Meta.fields + [
            "description", "preferred_visit_at", "received_at", "assigned_at",
            "started_at", "completed_at", "closed_at", "events", "worklogs",
        ]

    def get_worklogs(self, obj):
        user = self.context["request"].user
        qs = obj.worklogs.select_related("author").all()
        if not is_staff_member(user):
            qs = qs.filter(is_internal=False)
        return WorkLogSerializer(qs, many=True).data


class RequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = [
            "title", "description", "department", "category", "location",
            "priority", "preferred_visit_at",
        ]

    def validate(self, data):
        dept = data.get("department")
        cat = data.get("category")
        if cat and dept and cat.department_id != dept.id:
            raise serializers.ValidationError(
                {"category": "Category does not belong to the selected department."}
            )
        user = self.context["request"].user
        loc = data.get("location")
        if loc and loc.owner_id != user.id and not is_staff_member(user):
            raise serializers.ValidationError({"location": "That is not your property."})
        return data


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkLog
        fields = ["body", "is_internal"]


class AssignSerializer(serializers.Serializer):
    technician = serializers.IntegerField()


class NotificationSerializer(serializers.ModelSerializer):
    request_reference = serializers.CharField(
        source="request.reference", read_only=True, default=None
    )

    class Meta:
        model = Notification
        fields = ["id", "text", "is_read", "created_at", "request", "request_reference"]
