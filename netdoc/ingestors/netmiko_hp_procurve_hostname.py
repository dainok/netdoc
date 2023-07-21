"""Ingestor for netmiko_cisco_ios_hostname."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

<<<<<<< HEAD
import re
=======
from netmiko.utilities import get_structured_data
>>>>>>> 65cb3d6a9c7166c52089c9d4d3f4314a1fc4e7d2

from netdoc.schemas import device, discoverable
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    # See https://github.com/netbox-community/devicetype-library/tree/master/device-types
    vendor = "HPE"
    name = log.parsed_output

    # Parsing hostname
    try:
        name = re.findall(r".*System Name\s*:\s*(\S+).*$", name, re.MULTILINE | re.DOTALL).pop()
    except AttributeError as exc:
<<<<<<< HEAD
        raise AttributeError(f"Failed to match HOSTNAME regex on {name}") from exc
=======
        raise AttributeError("Failed to decode HOSTNAME") from exc
    if not name:
        raise AttributeError("Failed to decode HOSTNAME")

>>>>>>> 65cb3d6a9c7166c52089c9d4d3f4314a1fc4e7d2
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
