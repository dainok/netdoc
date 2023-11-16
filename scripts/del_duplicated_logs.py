"""Delete duplicated DiscoveryLogs.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < del_duplicated_logs.py
"""
from django.db.models import Count

from netdoc.models import DiscoveryLog

# Delete failed logs
# DiscoveryLog.objects.filter(success=False, configuration=False).delete()

# Delete duplicated logs (keep the recent ones)
logs = (
    DiscoveryLog.objects.all()
    .values("command", "discoverable__address")
    .annotate(total=Count("command"))
    .filter(total__gt=1)
    .order_by("-total")
)
for log in logs:
    log_o = (
        DiscoveryLog.objects.filter(
            discoverable__address=log.get("discoverable__address"),
            command=log.get("command"),
        )
        .order_by("created")
        .last()
    )
    DiscoveryLog.objects.filter(
        discoverable__address=log.get("discoverable__address"),
        command=log.get("command"),
        created__lt=log_o.created,
    ).delete()
