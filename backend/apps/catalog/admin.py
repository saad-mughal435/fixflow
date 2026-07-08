from django.contrib import admin

from .models import Department, ServiceCategory


class ServiceCategoryInline(admin.TabularInline):
    model = ServiceCategory
    extra = 0
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ServiceCategoryInline]


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "is_active")
    list_filter = ("department", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
