from django.db import models


class Department(models.Model):
    """A skill group / working group (Plumbing, Electrical, HVAC…).

    A Department is three things at once: the option a customer selects when
    raising a request, the receiving inbox for that request, and the skill a
    technician must hold to be assigned. ``code`` is the request-reference
    prefix (e.g. PLM-0001).
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    code = models.CharField(max_length=8, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ServiceCategory(models.Model):
    """A type of work within a department (e.g. Plumbing > "Blocked drain")."""

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=140, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["department__name", "name"]
        verbose_name_plural = "service categories"

    def __str__(self) -> str:
        return f"{self.department.name} > {self.name}"
