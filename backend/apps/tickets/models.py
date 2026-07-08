from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.tickets.choices import TERMINAL_STATUSES, EventVerb, Priority, Status


class Request(models.Model):
    """A property-maintenance service request, tracked through its lifecycle.

    Raised by a customer who selects the ``department`` (skill group). The
    request lands in that department's inbox; a dispatcher assigns a technician
    who holds that skill; the technician works it to completion.
    """

    reference = models.CharField(max_length=16, unique=True, blank=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        "catalog.Department",
        on_delete=models.PROTECT,
        related_name="requests",
    )
    category = models.ForeignKey(
        "catalog.ServiceCategory",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requests",
    )
    location = models.ForeignKey(
        "accounts.Property",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requests",
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_requests",
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_requests",
    )
    status = models.CharField(max_length=20, choices=Status, default=Status.SUBMITTED)
    priority = models.CharField(
        max_length=20, choices=Priority, default=Priority.P3_ROUTINE
    )
    sla_policy = models.ForeignKey(
        "sla.SlaPolicy",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requests",
    )
    sla_due_at = models.DateTimeField(null=True, blank=True)
    sla_breached = models.BooleanField(default=False)
    preferred_visit_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    received_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "priority"])]

    def __str__(self) -> str:
        return f"{self.reference or 'NEW'} {self.title}"

    @property
    def is_open(self) -> bool:
        return self.status not in TERMINAL_STATUSES

    def evaluate_sla(self, *, persist: bool = True) -> bool:
        """Recompute ``sla_breached`` from the due time and resolution state."""
        if self.sla_due_at is None:
            self.sla_breached = False
        else:
            endpoint = self.completed_at or timezone.now()
            self.sla_breached = endpoint > self.sla_due_at
        if persist and self.pk:
            type(self).objects.filter(pk=self.pk).update(sla_breached=self.sla_breached)
        return self.sla_breached

    def save(self, *args, **kwargs):
        from apps.sla.models import SlaPolicy

        creating = self._state.adding
        if creating:
            if self.sla_policy is None:
                self.sla_policy = SlaPolicy.for_priority(self.priority)
            if self.sla_due_at is None and self.sla_policy is not None:
                self.sla_due_at = self.sla_policy.resolution_due_from(timezone.now())
        self.evaluate_sla(persist=False)
        super().save(*args, **kwargs)
        if not self.reference:
            prefix = self.department.code if self.department_id else "REQ"
            new_ref = f"{prefix}-{self.pk:04d}"
            type(self).objects.filter(pk=self.pk).update(reference=new_ref)
            self.reference = new_ref
        if creating:
            self.log_event(EventVerb.CREATED, actor=self.requester)

    # --- audit -------------------------------------------------------------

    def log_event(self, verb, *, actor=None, from_value="", to_value=""):
        return RequestEvent.objects.create(
            request=self,
            actor=actor,
            verb=verb,
            from_value=from_value or "",
            to_value=to_value or "",
        )

    # --- transitions (each records an audit event + notifies) --------------

    def receive(self, *, actor=None):
        if self.status != Status.SUBMITTED:
            return
        self.status = Status.RECEIVED
        self.received_at = timezone.now()
        self.save()
        self.log_event(EventVerb.RECEIVED, actor=actor)
        send_notification(
            self.requester, self, f"{self.reference} received by {self.department}."
        )

    def assign_to(self, technician, *, actor=None):
        """Assign a technician. Guard: the technician must hold this skill.

        The availability filter lives in ``services.assign_request``; this model
        method enforces the hard correctness rule (skill membership) so it can
        never be bypassed.
        """
        if technician is not None:
            profile = getattr(technician, "staff_profile", None)
            if profile is None or not profile.departments.filter(
                pk=self.department_id
            ).exists():
                raise ValidationError(
                    f"{technician.get_username()} is not in the "
                    f"{self.department} skill group."
                )
        self.assignee = technician
        if self.status in (Status.SUBMITTED, Status.RECEIVED, Status.ON_HOLD):
            self.status = Status.ASSIGNED
            self.assigned_at = timezone.now()
            if self.received_at is None:
                self.received_at = timezone.now()
        self.save()
        self.log_event(
            EventVerb.ASSIGNED,
            actor=actor,
            to_value=technician.get_username() if technician else "",
        )
        if technician is not None and technician != actor:
            send_notification(
                technician, self, f"You were assigned {self.reference}: {self.title}"
            )

    def start(self, *, actor=None):
        if self.status != Status.ASSIGNED:
            return
        self.status = Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()
        self.log_event(EventVerb.STARTED, actor=actor)
        send_notification(self.requester, self, f"Work started on {self.reference}.")

    def hold(self, *, actor=None):
        if self.status != Status.IN_PROGRESS:
            return
        self.status = Status.ON_HOLD
        self.save()
        self.log_event(EventVerb.HELD, actor=actor)
        send_notification(self.requester, self, f"{self.reference} is on hold.")

    def resume(self, *, actor=None):
        if self.status != Status.ON_HOLD:
            return
        self.status = Status.IN_PROGRESS
        self.save()
        self.log_event(EventVerb.RESUMED, actor=actor)

    def mark_completed(self, *, actor=None):
        self.status = Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()
        self.log_event(EventVerb.COMPLETED, actor=actor)
        send_notification(
            self.requester, self, f"{self.reference} completed — please confirm."
        )

    def mark_closed(self, *, actor=None):
        self.status = Status.CLOSED
        self.closed_at = timezone.now()
        if self.completed_at is None:
            self.completed_at = self.closed_at
        self.save()
        self.log_event(EventVerb.CLOSED, actor=actor)

    def cancel(self, *, actor=None):
        self.status = Status.CANCELLED
        self.save()
        self.log_event(EventVerb.CANCELLED, actor=actor)

    def reopen(self, *, actor=None):
        self.status = Status.IN_PROGRESS if self.assignee_id else Status.RECEIVED
        self.completed_at = None
        self.closed_at = None
        self.save()
        self.log_event(EventVerb.REOPENED, actor=actor)
        if self.assignee_id and self.assignee != actor:
            send_notification(self.assignee, self, f"{self.reference} was reopened.")


class WorkLog(models.Model):
    """A comment / worklog entry on a request. Internal notes are staff-only."""

    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name="worklogs"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="worklogs",
    )
    body = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"WorkLog on {self.request.reference} by {self.author_id}"


class RequestEvent(models.Model):
    """An immutable audit entry forming the request timeline."""

    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name="events"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="request_events",
    )
    verb = models.CharField(max_length=20, choices=EventVerb)
    from_value = models.CharField(max_length=100, blank=True)
    to_value = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.request.reference}: {self.verb}"


class Notification(models.Model):
    """An in-app notification for a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    request = models.ForeignKey(
        Request,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    text = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"To {self.user_id}: {self.text}"


def send_notification(recipient, request, text, *, email=False):
    """Create an in-app notification and optionally an email (best-effort)."""
    if recipient is None:
        return
    Notification.objects.create(user=recipient, request=request, text=text)
    if email and getattr(recipient, "email", ""):
        from django.core.mail import send_mail

        send_mail(
            subject=(f"[{request.reference}] {text}" if request else text),
            message=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=True,
        )
