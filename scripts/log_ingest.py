"""Reparse all DiscoveryLogs.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < log_ingest.py
"""
from netdoc.models import DiscoveryLog
from netdoc.utils import log_ingest

FILTERS = ["172.25.82.50"]  # List of discoverable IP addresses
FILTERS = []

if FILTERS:
    logs = DiscoveryLog.objects.filter(discoverable__address__in=FILTERS).order_by(
        "order"
    )
else:
    logs = DiscoveryLog.objects.all().order_by("order")

# Edit the following lines to select what to ingest
logs = logs.filter(parsed=True)
logs = logs.filter(id=477)
# logs = logs.filter(ingested=False)
# logs = logs.filter(command="show mac address-table dynamic")

for log in logs:
    print(
        f"Reingesting log {log.id} with command {log.command} on device {log.discoverable}... ",
        end="",
    )
    log_ingest(log)
    print("done")
    log.ingested = True
    log.save()
