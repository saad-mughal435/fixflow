import pytest
from django.contrib.auth import get_user_model

from apps.tickets.permissions import role_of, visible_requests

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_customer_sees_only_own(make_request, customer, groups):
    other = User.objects.create_user("other", password="pw")
    other.groups.add(groups["customers"])
    mine = make_request()
    theirs = make_request(requester=other)
    vis = visible_requests(customer)
    assert mine in vis
    assert theirs not in vis


def test_technician_sees_only_assigned(make_request, make_technician, dept):
    assigned = make_request()
    tech = make_technician("t", [dept])
    assigned.assign_to(tech)
    unassigned = make_request()
    vis = visible_requests(tech)
    assert assigned in vis
    assert unassigned not in vis


def test_dispatcher_sees_only_their_departments(make_request, make_dispatcher, dept, dept2):
    r = make_request()  # in dept (PLM)
    other_dept_disp = make_dispatcher("d1", [dept2])
    assert r not in visible_requests(other_dept_disp)
    same_dept_disp = make_dispatcher("d2", [dept])
    assert r in visible_requests(same_dept_disp)


def test_manager_sees_all(make_request, groups):
    manager = User.objects.create_user("m", password="pw")
    manager.groups.add(groups["managers"])
    assert make_request() in visible_requests(manager)


def test_role_of(customer, make_technician, make_dispatcher, dept):
    assert role_of(customer) == "customer"
    assert role_of(make_technician("t", [dept])) == "technician"
    assert role_of(make_dispatcher("d", [dept])) == "dispatcher"
