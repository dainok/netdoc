"""Ingestor for netmiko_cisco_ios_show_interfaces_switchport."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device

    for item in log.parsed_output:
        interface_name = item.get("interface")
        label = utils.normalize_interface_label(interface_name)
        mode = utils.normalize_interface_mode(item.get("mode"))
        native_vlan = (
            int(item.get("native_vlan")) if item.get("native_vlan") != "None" else None
        )
        tagged_vlans = utils.normalize_vlan_list(item.get("trunking_vlans"))

        # Get or create Interface
        interface_o = interface.get(device_id=device_o.id, label=label)
        if not interface_o:
            interface_data = {
                "name": label,
                "device_id": device_o.id,
            }
            interface_o = interface.create(**interface_data)

        # Update Interface mode
        mode_data = {
            "untagged_vlan": native_vlan,
            "mode": mode,
            "tagged_vlans": tagged_vlans,
        }
        interface.update_mode(interface_o, **mode_data)

    # Update the log
    log.ingested = True
    log.save()
