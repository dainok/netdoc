"""Ingestor for netmiko_allied_telesis_awplus_show_mac_address-table."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2024, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface, macaddresstableentry
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device

    for item in log.parsed_output:
        if not item.get("port"):
            # Skip entries without associated interfaces
            continue
        interface_name = item.get("port")
        label = utils.normalize_interface_label(interface_name)
        vlan_id = int(item.get("vlan_id"))
        mac_address = utils.normalize_mac_address(item.get("mac"))

        interface_o = interface.get(device_id=device_o.id, label=label)
        if not interface_o:
            interface_data = {
                "name": label,
                "device_id": device_o.id,
            }
            interface_o = interface.create(**interface_data)

        macaddresstableentry_o = macaddresstableentry.get(
            interface_id=interface_o.id, vvid=vlan_id, mac_address=mac_address
        )
        if not macaddresstableentry_o:
            data = {
                "interface_id": interface_o.id,
                "vvid": vlan_id,
                "mac_address": mac_address,
            }
            macaddresstableentry.create(**data)

    # Update the log
    log.ingested = True
    log.save()
