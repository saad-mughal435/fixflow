from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CustomerProfile, Property, StaffProfile

User = get_user_model()


class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False
    filter_horizontal = ("departments",)
    extra = 0


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = [StaffProfileInline, CustomerProfileInline]
    list_display = ("username", "email", "is_staff", "is_active")


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("label", "property_type", "community", "city", "owner", "is_active")
    list_filter = ("property_type", "city", "is_active")
    search_fields = ("label", "address_line", "owner__username")
