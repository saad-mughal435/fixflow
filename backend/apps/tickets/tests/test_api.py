import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db
User = get_user_model()


def auth(client, user):
    client.force_authenticate(user=user)
    return client


def test_register_returns_customer_and_tokens(api_client):
    resp = api_client.post(
        "/api/auth/register/",
        {"username": "newc", "email": "n@example.ae", "password": "Str0ngPass!23"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["user"]["role"] == "customer"
    assert "access" in resp.data and "refresh" in resp.data


def test_login_returns_tokens_and_role(api_client, customer):
    resp = api_client.post(
        "/api/auth/login/", {"username": "cust", "password": "pw"}, format="json"
    )
    assert resp.status_code == 200
    assert "access" in resp.data
    assert resp.data["user"]["role"] == "customer"


def test_me_requires_auth(api_client):
    assert api_client.get("/api/auth/me/").status_code == 401


def test_customer_creates_and_lists_own(api_client, customer, dept, category, prop):
    auth(api_client, customer)
    payload = {
        "title": "Leak under sink", "department": dept.id, "category": category.id,
        "location": prop.id, "priority": "p3_routine", "description": "dripping",
    }
    resp = api_client.post("/api/requests/", payload, format="json")
    assert resp.status_code == 201, resp.data
    ref = resp.data["reference"]
    assert ref.startswith(dept.code)
    lst = api_client.get("/api/requests/")
    assert ref in [r["reference"] for r in lst.data["results"]]


def test_customer_cannot_see_others(api_client, make_request, customer, groups):
    other = User.objects.create_user("o", password="pw")
    other.groups.add(groups["customers"])
    theirs = make_request(requester=other)
    auth(api_client, customer)
    lst = api_client.get("/api/requests/")
    assert theirs.reference not in [r["reference"] for r in lst.data["results"]]


def test_dispatcher_assign_skill_match(api_client, make_request, make_dispatcher, make_technician, dept):
    req = make_request()
    disp = make_dispatcher("d", [dept])
    tech = make_technician("t", [dept])
    auth(api_client, disp)
    resp = api_client.post(
        f"/api/requests/{req.reference}/assign/", {"technician": tech.id}, format="json"
    )
    assert resp.status_code == 200, resp.data
    req.refresh_from_db()
    assert req.assignee_id == tech.id and req.status == "assigned"


def test_dispatcher_assign_wrong_skill_400(api_client, make_request, make_dispatcher, make_technician, dept, dept2):
    req = make_request()
    disp = make_dispatcher("d", [dept])
    tech = make_technician("t", [dept2])
    auth(api_client, disp)
    resp = api_client.post(
        f"/api/requests/{req.reference}/assign/", {"technician": tech.id}, format="json"
    )
    assert resp.status_code == 400


def test_eligible_technicians_endpoint(api_client, make_request, make_dispatcher, make_technician, dept, dept2):
    req = make_request()
    disp = make_dispatcher("d", [dept])
    good = make_technician("g", [dept])
    bad = make_technician("b", [dept2])
    auth(api_client, disp)
    resp = api_client.get(f"/api/requests/{req.reference}/eligible-technicians/")
    ids = [t["id"] for t in resp.data]
    assert good.id in ids and bad.id not in ids


def test_technician_lifecycle(api_client, make_request, make_technician, dept):
    req = make_request()
    tech = make_technician("t", [dept])
    req.assign_to(tech)
    auth(api_client, tech)
    assert api_client.post(f"/api/requests/{req.reference}/start/").status_code == 200
    assert api_client.post(f"/api/requests/{req.reference}/complete/").status_code == 200
    req.refresh_from_db()
    assert req.status == "completed"


def test_customer_cannot_assign(api_client, make_request, customer, make_technician, dept):
    req = make_request()
    tech = make_technician("t", [dept])
    auth(api_client, customer)
    resp = api_client.post(
        f"/api/requests/{req.reference}/assign/", {"technician": tech.id}, format="json"
    )
    assert resp.status_code == 403


def test_customer_only_sees_public_worklogs(api_client, make_request, make_technician, dept, customer):
    req = make_request()
    tech = make_technician("t", [dept])
    req.assign_to(tech)
    req.worklogs.create(author=tech, body="internal note", is_internal=True)
    req.worklogs.create(author=tech, body="public update", is_internal=False)
    auth(api_client, customer)
    resp = api_client.get(f"/api/requests/{req.reference}/")
    bodies = [w["body"] for w in resp.data["worklogs"]]
    assert "public update" in bodies and "internal note" not in bodies


def test_departments_list(api_client, customer, dept):
    auth(api_client, customer)
    resp = api_client.get("/api/departments/")
    assert resp.status_code == 200
    assert any(d["code"] == dept.code for d in resp.data)


def test_metrics_requires_staff(api_client, customer, manager):
    auth(api_client, customer)
    assert api_client.get("/api/metrics/dashboard/").status_code == 403
    auth(api_client, manager)
    assert api_client.get("/api/metrics/dashboard/").status_code == 200
