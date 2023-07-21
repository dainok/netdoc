"""Ingestor for netmiko_cisco_ios_hostname."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import re
from netmiko.utilities import get_structured_data

from netdoc.schemas import device, discoverable
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    # See https://github.com/netbox-community/devicetype-library/tree/master/device-types
    vendor = "HPE"
    platform = "hp_procurve"

    # Applying NTC Template
    log.parsed_output = get_structured_data(log.raw_output, platform, "show system")
    try:
        name = log.parsed_output[0].get("name")
    except AttributeError as exc:
        raise AttributeError(f"Failed to decode HOSTNAME") from exc
    if not name:
        raise AttributeError(f"Failed to decode HOSTNAME") from exc

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

