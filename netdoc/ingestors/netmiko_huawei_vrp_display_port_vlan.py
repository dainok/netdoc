"""Ingestor for netmiko_huawei_vrpdisplay_port_vlan."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device

    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/huawei_vrp/display_port_vlan # pylint: disable=line-too-long
        if item.get("link_type") == "desirable":
            # Skip interface with desirable mode
            continue
        interface_name = item.get("interface")
        label = utils.normalize_interface_label(interface_name)
        mode = utils.normalize_interface_mode(item.get("link_type"))
        native_vlan = int(item.get("pvid")) if item.get("pvid") else None
        tagged_vlans = utils.normalize_vlan_list(item.get("trunk_vlan_list"))

        # Get or create Interface
        interface_o = interface.get(device_id=device_o.id, label=label)
        if not interface_o:
            interface_data = {
                "name": label,
                "device_id": device_o.id,
            }
            interface_o = interface.create(**interface_data)

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
