"""Ingestor for netmiko_hp_comware_display_device_manuinfo."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device

    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/blob/master/tests/hp_comware/display_device_manuinfo/hp_comware_display_device_manuinfo.yml # pylint: disable=line-too-long
        part_description = item.get("slot_type")
        part_serial_number = item.get("device_serial_number")
        # part_id = item.get("device_name")

        if "chassis" in part_description.lower():
            # Chassis Serial Number
            device_o.serial = part_serial_number
            device_o.save()
            break

    # Update the log
    log.ingested = True
    log.save()
