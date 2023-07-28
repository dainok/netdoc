"""Run discovery directly (without RQ).

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < run_discovery_immediate.py
"""

from netdoc.models import Discoverable
from netdoc.tasks import discovery

FILTERS = ["172.25.82.45"]  # List of discoverable IP addresses
FILTERS = []
UNDISCOVERED_ONLY=True # Ignore FILTERS

# Don't edit below this line


def main():
    """Main function."""
    if UNDISCOVERED_ONLY:
        discoverable_addresss = list(Discoverable.objects.filter(last_discovered_at=None).values_list("address", flat=True))
        discovery(discoverable_addresss)
    else:
        discovery(FILTERS)


if __name__ == "django.core.management.commands.shell":
    main()
