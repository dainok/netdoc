"""Ingestor for netmiko_allied_telesis_show_system."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2024, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import device, discoverable
from netdoc import utils

# See: https://github.com/netbox-community/devicetype-library
MANUFACTURER = "Allied Telesis"
DEFAULT_MODEL = "Allied Telesis Unknown Device"


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device
    part_number = DEFAULT_MODEL
    part_serial_number = None

    for item in log.parsed_output:
        part_number = item.get("name")
        part_description = item.get("descr")
        part_serial_number = item.get("sn")
        description = item.get("software")
        hostname = item.get("hostname")
        hostname = utils.normalize_hostname(hostname)

        if "chassis" in part_description.lower():
            # Chassis model and Serial Number
            part_serial_number = item.get("sn")
            part_number = item.get("pid")
            break

    # Get or create Device
    data = {
        "name": hostname,
        "site_id": log.discoverable.site.id,
        "manufacturer": MANUFACTURER,
        "serial": part_serial_number,
        "model_keyword": part_number,
        "description": description,
    }
    device_o = device.get(name=data.get("name"))
    if not device_o:
        device_o = device.create(**data)

    if not log.discoverable.device:
        # Link Device to Discoverable
        discoverable.update(log.discoverable, device_id=device_o.id)

    device.update(
        device_o,
        serial=part_serial_number,
        manufacturer=MANUFACTURER,
        model_keyword=part_number,
        description=description,
    )

    # Update the log
    log.ingested = True
    log.save()
