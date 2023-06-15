"""Reparse all DiscoveryLogs.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < parse.py
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

logs = logs.filter(parsed=True)
# logs = logs.filter(id=1308)
# logs = logs.filter(ingested=False)
# logs = logs.filter(id=3)
# logs = logs.filter(command="show mac address-table dynamic")
# logs = logs.filter(ingested=False)

# log_list = []
# log_list.extend(logs)
# log_list.extend(logs.filter(template="HOSTNAME"))
# log_list.extend(logs.filter(command="arp -an"))
# log_list.extend(logs.filter(id=6710))

for log in logs:
    print(
        f"Reingesting log {log.id} with command {log.command} on device {log.discoverable}... ",
        end="",
    )
    log_ingest(log)
    print("done")
    log.ingested = True
    log.save()
