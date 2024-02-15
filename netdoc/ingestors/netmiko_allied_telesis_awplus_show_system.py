"""Ingestor for netmiko_allied_telesis_show_system."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2024, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import device

# See: https://github.com/netbox-community/devicetype-library
MANUFACTURER = "Allied Telesis"
DEFAULT_MODEL = "Allied Telesis Unknown Device"


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device
    part_number = DEFAULT_MODEL
    part_serial_number = None

    for item in log.parsed_output:
        part_serial_number = item.get("serial")
        part_number = item.get("hardware")

    device.update(
        device_o,
        serial=part_serial_number,
        manufacturer=MANUFACTURER,
        model_keyword=part_number,
    )

    # Update the log
    log.ingested = True
    log.save()
