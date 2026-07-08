"""Domain services — the skill-based assignment routing.

``eligible_technicians`` and ``assign_request`` are the load-bearing routing
rules and the centerpiece of the unit tests: a technician can only be assigned
to a request whose department is one of their skill groups (and they must be
available).
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


def eligible_technicians(department):
    """Technicians who hold ``department`` as a skill and are available."""
    return (
        User.objects.filter(
            groups__name="technicians",
            staff_profile__departments=department,
            staff_profile__is_available=True,
        )
        .distinct()
        .order_by("username")
    )


def assign_request(request_obj, technician, *, actor=None):
    """Assign ``technician`` to ``request_obj`` if they are eligible.

    Raises ``ValidationError`` if the technician lacks the department's skill or
    is unavailable. Delegates the state change + audit + notification to the
    model's ``assign_to`` (which independently enforces the skill guard).
    """
    if technician is None:
        raise ValidationError("A technician is required.")
    if not eligible_technicians(request_obj.department).filter(pk=technician.pk).exists():
        raise ValidationError(
            "That technician is not in this skill group or is unavailable."
        )
    request_obj.assign_to(technician, actor=actor)
    return request_obj
