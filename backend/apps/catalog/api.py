from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets

from apps.catalog.models import Department, ServiceCategory
from apps.catalog.serializers import DepartmentSerializer, ServiceCategorySerializer


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServiceCategory.objects.filter(is_active=True).select_related("department")
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["department"]
    pagination_class = None
