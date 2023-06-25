"""Parse a Netmiko log using low level functions.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < log_parse_ntc.py
"""
import pprint
from netmiko.utilities import get_structured_data

from netdoc.models import DiscoveryLog

LOG_ID = 661  # DiscoveryLog ID

# Don't edit below this line

log = DiscoveryLog.objects.get(id=LOG_ID)
platform = "_".join(  # pylint: disable=invalid-name
    log.discoverable.mode.split("_")[1:]
)
parsed_output = get_structured_data(log.raw_output, platform, log.template)
pprint.pprint(parsed_output)
