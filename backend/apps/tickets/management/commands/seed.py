"""Seed a realistic, idempotent FixFlow dataset (a UAE facilities-management
company). Safe to re-run: reference data is upserted; requests are only
generated when the table is empty unless ``--flush`` is passed.

    python manage.py seed          # create if empty
    python manage.py seed --flush  # wipe requests + regenerate
"""

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import CustomerProfile, Property, StaffProfile
from apps.catalog.models import Department, ServiceCategory
from apps.sla.models import SlaPolicy
from apps.tickets.choices import EventVerb, Priority, Status
from apps.tickets.models import Request, RequestEvent, WorkLog

User = get_user_model()
PASSWORD = "demo12345"

DEPARTMENTS = [
    ("Plumbing", "PLM", ["Blocked drain", "Leak / burst pipe", "Water heater", "Low pressure"]),
    ("Electrical", "ELE", ["Power trip", "Socket / switch", "Lighting", "DB board"]),
    ("HVAC / AC", "HVC", ["Not cooling", "AC water leak", "Servicing", "Noise / vibration"]),
    ("Carpentry", "CRP", ["Door / hinge", "Wardrobe", "Cabinet", "Skirting / trim"]),
    ("Painting", "PNT", ["Touch-up", "Full repaint", "Water-stain patch"]),
    ("Cleaning", "CLN", ["Deep clean", "Move-out clean", "Facade / windows"]),
    ("Appliance repair", "APP", ["Washing machine", "Refrigerator", "Oven / cooker", "Dishwasher"]),
    ("Handyman", "GEN", ["Mounting / fixing", "General repair", "Flat-pack assembly"]),
    ("Pest control", "PST", ["Ants / roaches", "Bed bugs", "Rodents"]),
    ("Landscaping", "LND", ["Garden upkeep", "Irrigation", "Tree / hedge"]),
]

SLA_DEFS = [
    ("Emergency response", Priority.P1_EMERGENCY, 30, 240, False),
    ("Urgent response", Priority.P2_URGENT, 60, 480, False),
    ("Routine response", Priority.P3_ROUTINE, 120, 1440, True),
    ("Low priority", Priority.P4_LOW, 240, 2880, False),
]

DISPATCHERS = [
    ("dispatcher", "Layla Hassan", ["PLM", "ELE", "HVC", "APP"]),
    ("dispatcher2", "Omar Farooq", ["CRP", "PNT", "CLN", "GEN", "PST", "LND"]),
]

TECHNICIANS = [
    ("tech.ahmed", "Ahmed Rahman", ["HVC", "ELE"], True),
    ("tech.ravi", "Ravi Kumar", ["PLM", "GEN"], True),
    ("tech.suresh", "Suresh Nair", ["ELE", "APP"], True),
    ("tech.bilal", "Bilal Khan", ["CRP", "PNT", "GEN"], True),
    ("tech.jomon", "Jomon Thomas", ["PLM", "HVC"], True),
    ("tech.samir", "Samir Haddad", ["CLN", "PST"], True),
    ("tech.deepak", "Deepak Sharma", ["APP", "ELE"], True),
    ("tech.faisal", "Faisal Al-Amri", ["PNT", "CRP"], True),
    ("tech.anil", "Anil Menon", ["LND", "GEN"], True),
    ("tech.tariq", "Tariq Sayed", ["PST", "CLN"], False),  # unavailable — exercises the guard
    ("tech.grace", "Grace Dsouza", ["CLN", "GEN"], True),
    ("tech.imran", "Imran Malik", ["HVC", "APP", "ELE"], True),
]

CUSTOMERS = [
    ("customer", "Sara Ahmed", "sara@example.ae",
     [("Marina apt 1203", "apartment", "Dubai Marina", "Marina Gate Tower 2", "1203")]),
    ("fatima", "Fatima Ali", "fatima@example.ae",
     [("JVC villa", "villa", "Jumeirah Village Circle", "District 12, Street 4", "V-7")]),
    ("rashid", "Rashid Noor", "rashid@example.ae",
     [("Business Bay office", "office", "Business Bay", "Bay Square Building 5", "305")]),
    ("elena", "Elena Petrova", "elena@example.ae",
     [("Downtown apartment", "apartment", "Downtown Dubai", "Burj Vista Tower 1", "2410")]),
    ("daniel", "Daniel Cruz", "daniel@example.ae",
     [("Ranches villa", "villa", "Arabian Ranches", "Alvorada 3", "V-22")]),
    ("mona", "Mona Yousef", "mona@example.ae",
     [("JLT apartment", "apartment", "Jumeirah Lakes Towers", "Cluster D, DEC Tower", "1808")]),
]

STATUS_POOL = (
    [Status.SUBMITTED] * 8
    + [Status.RECEIVED] * 6
    + [Status.ASSIGNED] * 8
    + [Status.IN_PROGRESS] * 10
    + [Status.ON_HOLD] * 4
    + [Status.COMPLETED] * 8
    + [Status.CLOSED] * 14
    + [Status.CANCELLED] * 2
)
PRIORITY_POOL = (
    [Priority.P1_EMERGENCY] * 2
    + [Priority.P2_URGENT] * 5
    + [Priority.P3_ROUTINE] * 9
    + [Priority.P4_LOW] * 4
)


class Command(BaseCommand):
    help = "Seed FixFlow with realistic demo data (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Wipe requests + regenerate.")

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(20260707)
        groups = self._seed_groups()
        depts = self._seed_departments()
        self._seed_sla()
        self._seed_manager(groups)
        self._seed_dispatchers(groups, depts)
        techs = self._seed_technicians(groups, depts)
        customers = self._seed_customers(groups)

        if options["flush"]:
            Request.objects.all().delete()
        if Request.objects.exists():
            self.stdout.write(self.style.WARNING("Requests already exist — skipping generation (use --flush)."))
            self._summary()
            return

        self._seed_requests(depts, techs, customers)
        self._summary()

    # -- reference data ----------------------------------------------------

    def _seed_groups(self):
        groups = {}
        for name in ("customers", "dispatchers", "technicians", "managers"):
            groups[name], _ = Group.objects.get_or_create(name=name)
        # Managers can touch everything; dispatchers/technicians change requests.
        perms = Permission.objects.filter(
            content_type__app_label__in=["tickets", "accounts", "catalog", "sla"]
        )
        groups["managers"].permissions.set(perms)
        change_view = perms.filter(codename__regex=r"^(view|change|add)_")
        groups["dispatchers"].permissions.set(change_view.filter(content_type__app_label="tickets"))
        groups["technicians"].permissions.set(
            perms.filter(codename__in=["view_request", "change_request", "view_worklog", "add_worklog"])
        )
        return groups

    def _seed_departments(self):
        depts = {}
        for name, code, cats in DEPARTMENTS:
            dept, _ = Department.objects.update_or_create(
                code=code, defaults={"name": name, "slug": slugify(name), "is_active": True}
            )
            for cat in cats:
                ServiceCategory.objects.get_or_create(
                    department=dept, name=cat,
                    defaults={"slug": slugify(f"{code}-{cat}"), "is_active": True},
                )
            depts[code] = dept
        return depts

    def _seed_sla(self):
        for name, priority, resp, res, is_default in SLA_DEFS:
            SlaPolicy.objects.update_or_create(
                priority=priority,
                defaults={
                    "name": name, "response_minutes": resp, "resolution_minutes": res,
                    "is_active": True, "is_default": is_default,
                },
            )

    # -- users -------------------------------------------------------------

    def _mkuser(self, username, name, email, group, *, is_staff=False):
        first, _, last = name.partition(" ")
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "first_name": first, "last_name": last, "is_staff": is_staff},
        )
        if created:
            user.set_password(PASSWORD)
            user.save()
        user.groups.add(group)
        return user

    def _seed_manager(self, groups):
        self._mkuser("manager", "Nadia Karim", "manager@fixflow.ae", groups["managers"], is_staff=True)

    def _seed_dispatchers(self, groups, depts):
        for username, name, codes in DISPATCHERS:
            user = self._mkuser(username, name, f"{username}@fixflow.ae", groups["dispatchers"], is_staff=True)
            profile, _ = StaffProfile.objects.update_or_create(
                user=user, defaults={"title": "Dispatcher", "is_available": True}
            )
            profile.departments.set([depts[c] for c in codes])

    def _seed_technicians(self, groups, depts):
        techs = []
        for username, name, codes, available in TECHNICIANS:
            user = self._mkuser(username, name, f"{username}@fixflow.ae", groups["technicians"])
            profile, _ = StaffProfile.objects.update_or_create(
                user=user, defaults={"title": "Technician", "is_available": available}
            )
            profile.departments.set([depts[c] for c in codes])
            techs.append((user, set(codes), available))
        return techs

    def _seed_customers(self, groups):
        customers = []
        for username, name, email, props in CUSTOMERS:
            user = self._mkuser(username, name, email, groups["customers"])
            CustomerProfile.objects.get_or_create(
                user=user, defaults={"phone": f"+9715{random.randint(10000000, 99999999)}"}
            )
            plist = []
            for label, ptype, community, addr, unit in props:
                prop, _ = Property.objects.get_or_create(
                    owner=user, label=label,
                    defaults={
                        "property_type": ptype, "community": community, "address_line": addr,
                        "unit_number": unit, "city": "Dubai", "emirate": "Dubai",
                    },
                )
                plist.append(prop)
            customers.append((user, plist))
        return customers

    # -- requests ----------------------------------------------------------

    def _seed_requests(self, depts, techs, customers):
        dept_codes = list(depts.keys())
        n = 62
        for _ in range(n):
            code = random.choice(dept_codes)
            dept = depts[code]
            category = random.choice(list(dept.categories.all()))
            customer, plist = random.choice(customers)
            prop = random.choice(plist) if plist else None
            priority = random.choice(PRIORITY_POOL)
            status = random.choice(STATUS_POOL)
            created_offset = random.randint(0, 18)  # days ago

            req = Request(
                title=f"{category.name} — {prop.community if prop else 'site'}",
                description=random.choice([
                    "Please attend at the earliest convenience.",
                    "Issue started yesterday and is getting worse.",
                    "Recurring problem, needs a proper fix.",
                    "Tenant reports this affects daily use.",
                    "Available for access in the evenings.",
                ]),
                department=dept, category=category, location=prop,
                requester=customer, priority=priority, status=Status.SUBMITTED,
            )
            req.save()  # sets reference + SLA + CREATED event

            created_at = timezone.now() - timedelta(days=created_offset, hours=random.randint(0, 12))
            sla_due = created_at + timedelta(minutes=req.sla_policy.resolution_minutes) if req.sla_policy else None
            Request.objects.filter(pk=req.pk).update(created_at=created_at, sla_due_at=sla_due)
            req.created_at = created_at
            req.sla_due_at = sla_due

            self._advance(req, status, created_at, techs, dept, code)
            self._add_worklogs(req, customer)

    def _advance(self, req, target, created_at, techs, dept, code):
        if target == Status.SUBMITTED:
            req.save()
            req.evaluate_sla()
            return
        req.received_at = created_at + timedelta(hours=random.randint(1, 6))

        assignee = None
        if target in (Status.ASSIGNED, Status.IN_PROGRESS, Status.ON_HOLD,
                      Status.COMPLETED, Status.CLOSED):
            eligible = [u for (u, codes, avail) in techs if code in codes and avail]
            if eligible:
                assignee = random.choice(eligible)
                req.assignee = assignee
                req.assigned_at = req.received_at + timedelta(hours=random.randint(1, 10))
            else:
                target = Status.RECEIVED  # no available skilled tech → stays received

        if target in (Status.IN_PROGRESS, Status.ON_HOLD, Status.COMPLETED, Status.CLOSED):
            req.started_at = req.assigned_at + timedelta(hours=random.randint(1, 20))
        if target in (Status.COMPLETED, Status.CLOSED):
            req.completed_at = req.started_at + timedelta(hours=random.randint(1, 30))
        if target == Status.CLOSED:
            req.closed_at = req.completed_at + timedelta(hours=random.randint(1, 24))
        if target == Status.CANCELLED:
            pass

        req.status = target
        req.save()
        req.evaluate_sla()

        # a lightweight timeline
        if req.received_at:
            self._event(req, EventVerb.RECEIVED, req.received_at)
        if assignee:
            self._event(req, EventVerb.ASSIGNED, req.assigned_at, to=assignee.username)
        if req.started_at:
            self._event(req, EventVerb.STARTED, req.started_at)
        if req.completed_at:
            self._event(req, EventVerb.COMPLETED, req.completed_at)
        if req.closed_at:
            self._event(req, EventVerb.CLOSED, req.closed_at)

    def _event(self, req, verb, when, to=""):
        ev = RequestEvent.objects.create(request=req, verb=verb, to_value=to or "")
        RequestEvent.objects.filter(pk=ev.pk).update(created_at=when)

    def _add_worklogs(self, req, customer):
        for _ in range(random.randint(0, 2)):
            author = req.assignee or customer
            WorkLog.objects.create(
                request=req, author=author,
                body=random.choice([
                    "Attended site and diagnosed the issue.",
                    "Parts ordered; will return to complete.",
                    "Cleared and tested — working now.",
                    "Please confirm a convenient time for the visit.",
                ]),
                is_internal=bool(req.assignee and random.random() < 0.5),
            )

    def _summary(self):
        self.stdout.write(self.style.SUCCESS(
            f"Seeded: {Department.objects.count()} departments, "
            f"{User.objects.count()} users, {Request.objects.count()} requests."
        ))
        self.stdout.write(
            "Demo logins (password 'demo12345'): "
            "manager · dispatcher · tech.ahmed · customer"
        )
