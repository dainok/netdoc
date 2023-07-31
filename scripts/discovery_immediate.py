"""Run discovery directly (without RQ).

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < run_discovery_immediate.py
"""

from netdoc.models import Discoverable
from netdoc.tasks import discovery

FILTERS = ["172.25.82.45"]  # List of discoverable IP addresses
FILTERS = []
#FILTERS = list(Discoverable.objects.filter(device__name__contains="ME38").values_list("address", flat=True))
#FILTERS = list(Discoverable.objects.filter(last_discovered_at=None).values_list("address", flat=True))

# Don't edit below this line


def main():
    """Main function."""
    discovery(FILTERS)


if __name__ == "django.core.management.commands.shell":
    main()
