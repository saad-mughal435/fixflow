"""Root URL configuration.

  /admin/                 Django admin (staff config)
  /healthz /readyz        liveness / readiness probes
  /api/auth/…             JWT register / login / refresh / me
  /api/…                  DRF router: requests, departments, categories,
                          properties, notifications
  /api/metrics/dashboard/ role-scoped dashboard metrics
  /api/schema/…           OpenAPI schema + Swagger UI + ReDoc
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.api import LoginView, MeView, PropertyViewSet, RegisterView
from apps.catalog.api import DepartmentViewSet, ServiceCategoryViewSet
from apps.tickets.api import MetricsView, NotificationViewSet, RequestViewSet
from config.views import healthz, readyz

router = DefaultRouter()
router.register("requests", RequestViewSet, basename="request")
router.register("departments", DepartmentViewSet, basename="department")
router.register("categories", ServiceCategoryViewSet, basename="category")
router.register("properties", PropertyViewSet, basename="property")
router.register("notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz, name="healthz"),
    path("readyz", readyz, name="readyz"),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    path("api/metrics/dashboard/", MetricsView.as_view(), name="metrics"),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
