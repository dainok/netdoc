"""Ingestor for netmiko_hp_comware_display_interface."""
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
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/hp_comware/display_interface # pylint: disable=line-too-long
        interface_name = item.get("interface")
        label = utils.normalize_interface_label(interface_name)
        description = item.get("description")
        duplex = utils.normalize_interface_duplex(item.get("duplex"))
        speed = utils.normalize_interface_speed(item.get("bandwidth"))
        mac_address = (
            utils.normalize_mac_address(item.get("hw_address")[0])
            if item.get("hw_address")
            and not utils.incomplete_mac(item.get("hw_address")[0])
            else None
        )
        mode = utils.normalize_interface_mode(item.get("port_link_type"))
        int_type = utils.normalize_interface_type(item.get("interface"))
        enabled = (
            utils.normalize_interface_status(item.get("line_status"))
            if item.get("line_status")
            else None
        )
        mtu = utils.normalize_interface_mtu(item.get("mtu"))
        parent_name = utils.parent_interface(label)
        native_vlan = int(item.get("vlan_native")) if item.get("vlan_native") else None
        tagged_vlans = utils.normalize_vlan_list(item.get("vlan_permitted"))

        if parent_name:
            # Parent Interface is set
            parent_label = utils.normalize_interface_label(parent_name)
            parent_o = interface.get(device_id=device_o.id, label=parent_label)
            if not parent_o:
                parent_data = {
                    "name": parent_name,
                    "device_id": device_o.id,
                }
                parent_o = interface.create(**parent_data)

        data = {
            "name": interface_name,
            "description": description,
            "duplex": duplex,
            "speed": speed,
            "mac_address": mac_address,
            "type": int_type,
            "device_id": device_o.id,
            "enabled": enabled,
            "mtu": mtu,
            "parent_id": parent_o.id if parent_name else None,
        }

        interface_o = interface.get(device_id=device_o.id, label=label)
        if not interface_o:
            interface_o = interface.create(**data)
        else:
            interface_o = interface.update(interface_o, **data)

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
