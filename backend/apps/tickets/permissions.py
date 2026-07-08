"""Role-based permissions + queryset scoping, keyed off Django Groups.

Roles: ``customers`` (raise + track their own requests), ``dispatchers``
(receive + assign for their departments), ``technicians`` (work their assigned
jobs), ``managers`` (everything + config). Superusers pass every check.
"""

from django.conf import settings
from rest_framework import permissions

from apps.tickets.models import Request

CUSTOMERS = "customers"
DISPATCHERS = "dispatchers"
TECHNICIANS = "technicians"
MANAGERS = "managers"


def in_group(user, name: str) -> bool:
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or user.groups.filter(name=name).exists())
    )


def is_customer(user) -> bool:
    return in_group(user, CUSTOMERS)


def is_technician(user) -> bool:
    return in_group(user, TECHNICIANS)


def is_dispatcher(user) -> bool:
    return in_group(user, DISPATCHERS) or in_group(user, MANAGERS)


def is_manager(user) -> bool:
    return in_group(user, MANAGERS) or bool(user and user.is_superuser)


def is_staff_member(user) -> bool:
    return is_technician(user) or is_dispatcher(user) or is_manager(user)


def role_of(user) -> str:
    if not user or not user.is_authenticated:
        return "anonymous"
    if is_manager(user):
        return "manager"
    if is_dispatcher(user):
        return "dispatcher"
    if is_technician(user):
        return "technician"
    if is_customer(user):
        return "customer"
    return "customer"


def visible_requests(user):
    """The requests a user may see — the single scoping rule for every view."""
    qs = Request.objects.select_related(
        "requester", "assignee", "department", "category", "location"
    )
    if is_manager(user):
        return qs
    if is_dispatcher(user):
        depts = (
            user.staff_profile.departments.all() if hasattr(user, "staff_profile") else []
        )
        return qs.filter(department__in=depts)
    if is_technician(user):
        return qs.filter(assignee=user)
    return qs.filter(requester=user)


class IsCustomer(permissions.BasePermission):
    message = "This action requires a customer account."

    def has_permission(self, request, view):
        return is_customer(request.user)


class IsDispatcher(permissions.BasePermission):
    message = "This action requires a dispatcher account."

    def has_permission(self, request, view):
        return is_dispatcher(request.user)


class IsTechnician(permissions.BasePermission):
    message = "This action requires a technician account."

    def has_permission(self, request, view):
        return is_technician(request.user)


class IsManager(permissions.BasePermission):
    message = "This action requires a manager account."

    def has_permission(self, request, view):
        return is_manager(request.user)


class IsStaff(permissions.BasePermission):
    message = "This action requires a staff account."

    def has_permission(self, request, view):
        return is_staff_member(request.user)


class DemoModeDeleteGuard(permissions.BasePermission):
    """In DEMO_MODE, block deletes for everyone except a real superuser."""

    message = "Deleting records is disabled in the public demo."

    def has_permission(self, request, view):
        if (
            settings.DEMO_MODE
            and request.method == "DELETE"
            and not (request.user and request.user.is_superuser)
        ):
            return False
        return True
