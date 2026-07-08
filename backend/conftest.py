import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from apps.accounts.models import CustomerProfile, Property, StaffProfile
from apps.catalog.models import Department, ServiceCategory
from apps.sla.models import SlaPolicy
from apps.tickets.choices import Priority
from apps.tickets.models import Request

User = get_user_model()


@pytest.fixture
def groups(db):
    return {
        n: Group.objects.get_or_create(name=n)[0]
        for n in ("customers", "dispatchers", "technicians", "managers")
    }


@pytest.fixture
def dept(db):
    return Department.objects.create(name="Plumbing", slug="plumbing", code="PLM")


@pytest.fixture
def dept2(db):
    return Department.objects.create(name="Electrical", slug="electrical", code="ELE")


@pytest.fixture
def category(dept):
    return ServiceCategory.objects.create(department=dept, name="Leak", slug="plm-leak")


@pytest.fixture
def sla(db):
    return SlaPolicy.objects.create(
        name="Routine", priority=Priority.P3_ROUTINE,
        response_minutes=120, resolution_minutes=1440, is_default=True,
    )


@pytest.fixture
def customer(db, groups):
    user = User.objects.create_user("cust", password="pw", email="c@example.ae")
    user.groups.add(groups["customers"])
    CustomerProfile.objects.create(user=user)
    return user


@pytest.fixture
def prop(customer):
    return Property.objects.create(owner=customer, label="Apt 1", address_line="Marina")


@pytest.fixture
def make_technician(db, groups):
    def _make(username, departments, available=True):
        user = User.objects.create_user(username, password="pw")
        user.groups.add(groups["technicians"])
        profile = StaffProfile.objects.create(user=user, is_available=available)
        profile.departments.set(departments)
        return user
    return _make


@pytest.fixture
def make_dispatcher(db, groups):
    def _make(username, departments):
        user = User.objects.create_user(username, password="pw", is_staff=True)
        user.groups.add(groups["dispatchers"])
        profile = StaffProfile.objects.create(user=user)
        profile.departments.set(departments)
        return user
    return _make


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def manager(db, groups):
    user = User.objects.create_user("mgr", password="pw")
    user.groups.add(groups["managers"])
    return user


@pytest.fixture
def make_request(dept, category, customer, prop, sla):
    def _make(**kw):
        defaults = dict(
            title="Leak", department=dept, category=category, location=prop,
            requester=customer, priority=Priority.P3_ROUTINE,
        )
        defaults.update(kw)
        return Request.objects.create(**defaults)
    return _make
