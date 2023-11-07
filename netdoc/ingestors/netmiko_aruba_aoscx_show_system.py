"""Ingestor for netmiko_aruba_aoscx_show_system."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import device

# See: https://github.com/netbox-community/devicetype-library
MANUFACTURER = "HPE"


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device
    part_serial_number = None

    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/aruba_aoscx/show_system # pylint: disable=line-too-long
        part_description = item.get("product")
        part_serial_number = item.get("serial")

    device.update(
        device_o,
        serial=part_serial_number,
        manufacturer=MANUFACTURER,
        model_keyword=part_description,
    )

    # Update the log
    log.ingested = True
    log.save()
