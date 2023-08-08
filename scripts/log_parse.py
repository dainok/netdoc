"""Reparse all DiscoveryLogs.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < log_parse.py
"""
from netdoc.models import DiscoveryLog

FILTERS = ["172.25.82.44", "172.25.82.45"]  # List of discoverable IP addresses
FILTERS = ["127.0.0.1"]

REPARSE = True

# Don't edit below this line

logs = DiscoveryLog.objects.filter(success=True)
if not REPARSE:
    logs = logs.filter(parsed=False)
if FILTERS:
    logs = logs.filter(discoverable__address__in=FILTERS)

for log in logs:
    print(f"Reparsing log {log.id}...")
    log.parse()
    log.ingested = False
    log.save()
