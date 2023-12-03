"""Ingestor for netmiko_aruba_aoscx_show_interface."""
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
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/aruba_aoscx/show_interface # pylint: disable=line-too-long
        interface_name = item.get("interface")
        label = utils.normalize_interface_label(interface_name)
        description = item.get("interface_desc")
        duplex = utils.normalize_interface_duplex(item.get("duplex"))
        speed = utils.normalize_interface_speed(item.get("speed"))
        mac_address = (
            utils.normalize_mac_address(item.get("mac_address"))
            if not utils.incomplete_mac(item.get("mac_address"))
            else None
        )
        int_type = utils.normalize_interface_type(item.get("interface"))
        enabled = utils.normalize_interface_status(item.get("link_status"))
        mtu = utils.normalize_interface_mtu(item.get("mtu"))
        parent_name = utils.parent_interface(label)
        mode = utils.normalize_interface_mode(item.get("vlan_mode"))
        native_vlan = int(item.get("vlan_native")) if item.get("vlan_native") else None
        access_vlan = int(item.get("vlan_access")) if item.get("vlan_access") else None
        tagged_vlans = utils.normalize_vlan_list(item.get("vlan_trunk"))
        ip_addresses = [item.get("ip_address")] if item.get("ip_address") else []
        attached_interface_names = item.get("aggregated_interfaces")

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
            "untagged_vlan": access_vlan if mode == "access" else native_vlan,
            "mode": mode,
            "tagged_vlans": tagged_vlans,
        }
        interface.update_mode(interface_o, **mode_data)

        # Update Interface
        interface.update_addresses(interface_o, ip_addresses=ip_addresses)

        # LAG
        for attached_interface_name in attached_interface_names:
            attached_interface_label = utils.normalize_interface_label(
                attached_interface_name
            )
            attached_interface_o = interface.get(
                device_id=device_o.id, label=attached_interface_label
            )
            if not attached_interface_o:
                attached_interface_data = {
                    "name": attached_interface_name,
                    "device_id": device_o.id,
                }
                attached_interface_o = interface.create(**attached_interface_data)
            # Set LAG on attached Interface
            attached_interface_o = interface.update(
                attached_interface_o, lag_id=interface_o.id
            )

    # Update the log
    log.ingested = True
    log.save()
