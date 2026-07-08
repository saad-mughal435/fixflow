"""Dashboard metrics computed over a role-scoped request queryset."""

from collections import Counter
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.tickets.choices import TERMINAL_STATUSES, Status
from apps.tickets.permissions import visible_requests

User = get_user_model()


def dashboard_metrics(user):
    qs = visible_requests(user)
    rows = list(
        qs.values(
            "status", "priority", "sla_breached", "assignee_id",
            "assignee__username", "department__name", "created_at",
        )
    )
    open_rows = [r for r in rows if r["status"] not in TERMINAL_STATUSES]

    by_status = Counter(r["status"] for r in rows)
    by_priority = Counter(r["priority"] for r in open_rows)
    by_department = Counter(r["department__name"] for r in open_rows)
    workload = Counter(
        r["assignee__username"] for r in open_rows if r["assignee_id"]
    )

    now = timezone.now()
    volume = []
    for i in range(13, -1, -1):
        day = (now - timedelta(days=i)).date()
        count = sum(1 for r in rows if r["created_at"].date() == day)
        volume.append({"date": day.isoformat(), "count": count})

    return {
        "total": len(rows),
        "open": len(open_rows),
        "unassigned": sum(
            1 for r in open_rows if not r["assignee_id"] and r["status"] == Status.SUBMITTED
        ),
        "sla_breached": sum(1 for r in open_rows if r["sla_breached"]),
        "by_status": [{"status": k, "count": v} for k, v in by_status.items()],
        "by_priority": [{"priority": k, "count": v} for k, v in sorted(by_priority.items())],
        "by_department": sorted(
            [{"department": k, "count": v} for k, v in by_department.items()],
            key=lambda x: -x["count"],
        ),
        "technician_workload": sorted(
            [{"technician": k, "open": v} for k, v in workload.items()],
            key=lambda x: -x["open"],
        )[:10],
        "volume_14d": volume,
    }
