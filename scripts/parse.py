"""Reparse all DiscoveryLogs.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < parse.py
"""
from netdoc.models import DiscoveryLog

FILTERS = ["10.95.231.1"]  # List of discoverable IP addresses
FILTERS = []

logs = DiscoveryLog.objects.filter(parsed=False, success=True)
if FILTERS:
    logs = logs.filter(discoverable__address__in=FILTERS)

for log in logs:
    print(f"Reparsing log {log.id}...")
    log.parse()
    log.ingested = False
    log.save()
