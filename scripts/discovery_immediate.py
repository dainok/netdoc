"""Run discovery directly (without RQ).

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < run_discovery_immediate.py
"""

from netdoc.tasks import discovery

FILTERS = ["172.25.82.45"]  # List of discoverable IP addresses
FILTERS = ["127.0.0.1"]

# Don't edit below this line


def main():
    """Main function."""
    discovery(FILTERS)


if __name__ == "django.core.management.commands.shell":
    main()
