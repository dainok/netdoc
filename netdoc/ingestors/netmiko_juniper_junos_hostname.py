"""Ingestor for netmiko_juniper_junos_hostname."""
__author__ = "Andy Brown"
__contact__ = "andy@thebmwz3.co.uk"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

import re

from netdoc.schemas import device, discoverable
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    # See https://github.com/netbox-community/devicetype-library/tree/master/device-types
    vendor = "Juniper"
    name = log.parsed_output

    # Parsing hostname
    try:
        name = re.match(r".*Hostname:\ (\S+)$", name, re.MULTILINE | re.DOTALL).group(1)
    except AttributeError as exc:
        raise AttributeError(f"Failed to match HOSTNAME regex on {name}") from exc
    name = utils.normalize_hostname(name)

    # Get or create Device
    data = {
        "name": name,
        "site_id": log.discoverable.site.id,
        "manufacturer": vendor,
    }
    device_o = device.get(name=data.get("name"))
    if not device_o:
        device_o = device.create(**data)

    if not log.discoverable.device:
        # Link Device to Discoverable
        discoverable.update(log.discoverable, device_id=device_o.id)

    # Update the log
    log.ingested = True
    log.save()