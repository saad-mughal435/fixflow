from django.conf import settings
from django.db import models


class CustomerProfile(models.Model):
    """Attributes for a customer (the person who raises requests)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    phone = models.CharField(max_length=30, blank=True)
    company_name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.get_username()} (customer)"


class StaffProfile(models.Model):
    """Department-scoped internal staff (dispatchers + technicians).

    ``departments`` is the many-to-many core twist: for a TECHNICIAN it is the
    set of skill groups they can work (a person can do more than one job); for a
    DISPATCHER it is the set of inbox queues they coordinate.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )
    departments = models.ManyToManyField(
        "catalog.Department", related_name="staff", blank=True
    )
    title = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.user.get_username()} (staff)"


class Property(models.Model):
    """A location owned by a customer that maintenance is performed on."""

    class PropertyType(models.TextChoices):
        APARTMENT = "apartment", "Apartment"
        VILLA = "villa", "Villa"
        TOWNHOUSE = "townhouse", "Townhouse"
        OFFICE = "office", "Office"
        RETAIL = "retail", "Retail unit"
        WAREHOUSE = "warehouse", "Warehouse"
        BUILDING = "building", "Whole building"
        OTHER = "other", "Other"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="properties"
    )
    label = models.CharField(max_length=120)
    property_type = models.CharField(
        max_length=20, choices=PropertyType, default=PropertyType.APARTMENT
    )
    address_line = models.CharField(max_length=255)
    community = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=80, default="Dubai")
    emirate = models.CharField(max_length=40, blank=True)
    unit_number = models.CharField(max_length=40, blank=True)
    access_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["label"]
        verbose_name_plural = "properties"

    def __str__(self) -> str:
        return f"{self.label} — {self.city}"
