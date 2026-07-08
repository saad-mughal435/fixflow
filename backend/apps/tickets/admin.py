from django.contrib import admin

from .models import Notification, Request, RequestEvent, WorkLog


class RequestEventInline(admin.TabularInline):
    model = RequestEvent
    extra = 0
    can_delete = False
    readonly_fields = ("verb", "actor", "from_value", "to_value", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


class WorkLogInline(admin.TabularInline):
    model = WorkLog
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "title", "department", "status", "priority",
        "requester", "assignee", "sla_breached", "created_at",
    )
    list_filter = ("status", "priority", "department", "sla_breached")
    search_fields = ("reference", "title", "description")
    readonly_fields = ("reference", "created_at", "updated_at")
    raw_id_fields = ("requester", "assignee", "location", "category", "department", "sla_policy")
    inlines = [RequestEventInline, WorkLogInline]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "text", "is_read", "created_at")
    list_filter = ("is_read",)
