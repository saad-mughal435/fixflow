import pytest

from apps.tickets.choices import EventVerb, Status

pytestmark = pytest.mark.django_db


def test_reference_and_sla_on_create(make_request, dept):
    r = make_request()
    assert r.reference.startswith(dept.code + "-")
    assert r.sla_due_at is not None
    assert r.status == Status.SUBMITTED
    assert r.events.filter(verb=EventVerb.CREATED).exists()


def test_full_lifecycle(make_request, make_technician, dept):
    r = make_request()
    tech = make_technician("t1", [dept])
    r.receive()
    assert r.status == Status.RECEIVED and r.received_at is not None
    r.assign_to(tech)
    assert r.status == Status.ASSIGNED and r.assignee == tech and r.assigned_at is not None
    r.start()
    assert r.status == Status.IN_PROGRESS and r.started_at is not None
    r.hold()
    assert r.status == Status.ON_HOLD
    r.resume()
    assert r.status == Status.IN_PROGRESS
    r.mark_completed()
    assert r.status == Status.COMPLETED and r.completed_at is not None
    r.mark_closed()
    assert r.status == Status.CLOSED and r.closed_at is not None
    assert not r.is_open


def test_reopen_clears_timestamps(make_request, make_technician, dept):
    r = make_request()
    tech = make_technician("t1", [dept])
    r.assign_to(tech)
    r.start()
    r.mark_completed()
    r.mark_closed()
    r.reopen()
    assert r.status == Status.IN_PROGRESS
    assert r.completed_at is None and r.closed_at is None


def test_cancel(make_request):
    r = make_request()
    r.cancel()
    assert r.status == Status.CANCELLED and not r.is_open


def test_sla_breach_flag(make_request):
    from datetime import timedelta

    from django.utils import timezone

    r = make_request()
    r.sla_due_at = timezone.now() - timedelta(hours=1)
    r.save()
    assert r.evaluate_sla() is True
