"""Ingestor for netmiko_huawei_vrp_display_interface."""
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
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/huawei_vrp/display_interface # pylint: disable=line-too-long
        interface_name = item.get("interface")
        label = utils.normalize_interface_label(interface_name)
        description = item.get("description")
        duplex = utils.normalize_interface_duplex(item.get("duplex"))
        speed = (
            utils.normalize_interface_speed(f'{item.get("speed")}000')
            if item.get("speed")
            else None
        )
        mac_address = (
            utils.normalize_mac_address(item.get("hardware_address"))
            if not utils.incomplete_mac(item.get("hardware_address"))
            else None
        )
        int_type = utils.normalize_interface_type(item.get("interface"))
        enabled = utils.normalize_interface_status(item.get("link_status"))
        mtu = utils.normalize_interface_mtu(item.get("mtu"))
        parent_name = utils.parent_interface(label)
        ip_addresses = [item.get("internet_address")]
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
            interface.update(interface_o, **data)

        # Update Interface
        interface.update_addresses(interface_o, ip_addresses=ip_addresses)

        # Bundled interfaces
        for attached_interface_name in attached_interface_names:
            # Get or create attached Interface
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
