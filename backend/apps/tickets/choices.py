"""Shared enumerations for the maintenance-request domain.

Kept in a model-free module so other apps (e.g. ``sla``) can import the choices
without creating an app-loading import cycle.
"""

from django.db import models


class Status(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"          # customer created; in dept inbox
    RECEIVED = "received", "Received"             # dispatcher acknowledged
    ASSIGNED = "assigned", "Assigned"             # technician set
    IN_PROGRESS = "in_progress", "In progress"
    ON_HOLD = "on_hold", "On hold"
    COMPLETED = "completed", "Completed"          # technician done; awaiting close
    CLOSED = "closed", "Closed"
    CANCELLED = "cancelled", "Cancelled"


# Requests in these states are no longer counted as "open" / actionable.
TERMINAL_STATUSES = frozenset({Status.COMPLETED, Status.CLOSED, Status.CANCELLED})


class Priority(models.TextChoices):
    # Values sort lexicographically in priority order (p1 < p2 < p3 < p4).
    P1_EMERGENCY = "p1_emergency", "P1 - Emergency"
    P2_URGENT = "p2_urgent", "P2 - Urgent"
    P3_ROUTINE = "p3_routine", "P3 - Routine"
    P4_LOW = "p4_low", "P4 - Low"


class EventVerb(models.TextChoices):
    CREATED = "created", "Created"
    RECEIVED = "received", "Received"
    ASSIGNED = "assigned", "Assigned"
    STATUS_CHANGED = "status_changed", "Status changed"
    PRIORITY_CHANGED = "priority_changed", "Priority changed"
    COMMENTED = "commented", "Commented"
    STARTED = "started", "Started"
    HELD = "held", "Put on hold"
    RESUMED = "resumed", "Resumed"
    COMPLETED = "completed", "Completed"
    CLOSED = "closed", "Closed"
    CANCELLED = "cancelled", "Cancelled"
    REOPENED = "reopened", "Reopened"
