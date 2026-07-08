from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.tickets.choices import EventVerb
from apps.tickets.models import RequestEvent, WorkLog, send_notification


@receiver(post_save, sender=WorkLog)
def worklog_created(sender, instance, created, **kwargs):
    """Record a COMMENTED event and notify the other party on a new worklog."""
    if not created:
        return
    req = instance.request
    RequestEvent.objects.create(request=req, actor=instance.author, verb=EventVerb.COMMENTED)
    recipients = set()
    if (
        req.requester_id
        and req.requester != instance.author
        and not instance.is_internal
    ):
        recipients.add(req.requester)
    if req.assignee_id and req.assignee != instance.author:
        recipients.add(req.assignee)
    for recipient in recipients:
        send_notification(recipient, req, f"New update on {req.reference}")
