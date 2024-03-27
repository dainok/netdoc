"""Parse a Netmiko log using low level functions.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < log_parse_ntc.py
"""
import pprint
from netmiko.utilities import get_structured_data

from netdoc.models import DiscoveryLog

LOG_ID = 4139  # DiscoveryLog ID

# Don't edit below this line

log = DiscoveryLog.objects.get(id=LOG_ID)
if log.details.get("framework") != "netmiko":
    print(f"Log {LOG_ID} platform is not Netmiko")
platform = log.details.get("platform")
print(f"Parsing log {LOG_ID} with platform {platform} and template {log.template}")
parsed_output = get_structured_data(log.raw_output, platform, log.template)
pprint.pprint(parsed_output)
