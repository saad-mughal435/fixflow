"""The skill-based assignment guard — the load-bearing routing rule."""

import pytest
from django.core.exceptions import ValidationError

from apps.tickets.services import assign_request, eligible_technicians

pytestmark = pytest.mark.django_db


def test_eligible_only_skilled_and_available(make_request, make_technician, dept, dept2):
    skilled = make_technician("skilled", [dept])
    wrong_skill = make_technician("wrong", [dept2])
    unavailable = make_technician("unavail", [dept], available=False)
    elig = list(eligible_technicians(dept))
    assert skilled in elig
    assert wrong_skill not in elig
    assert unavailable not in elig


def test_multiskill_tech_eligible_for_each_skill(make_technician, dept, dept2):
    tech = make_technician("multi", [dept, dept2])
    assert tech in list(eligible_technicians(dept))
    assert tech in list(eligible_technicians(dept2))


def test_assign_request_succeeds_for_matched_tech(make_request, make_technician, dept):
    r = make_request()
    tech = make_technician("t", [dept])
    assign_request(r, tech, actor=None)
    r.refresh_from_db()
    assert r.assignee == tech
    assert r.status == "assigned"


def test_assign_request_rejects_wrong_skill(make_request, make_technician, dept2):
    r = make_request()
    tech = make_technician("t", [dept2])
    with pytest.raises(ValidationError):
        assign_request(r, tech)


def test_assign_request_rejects_unavailable(make_request, make_technician, dept):
    r = make_request()
    tech = make_technician("t", [dept], available=False)
    with pytest.raises(ValidationError):
        assign_request(r, tech)


def test_model_assign_guard_rejects_wrong_skill(make_request, make_technician, dept2):
    r = make_request()
    tech = make_technician("t", [dept2])
    with pytest.raises(ValidationError):
        r.assign_to(tech)
