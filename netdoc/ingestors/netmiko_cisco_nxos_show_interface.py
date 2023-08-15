"""Ingestor for netmiko_cisco_nxos_show_interface."""
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
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/cisco_nxos/show_interface # pylint: disable=line-too-long
        interface_name = item.get("interface")
        label = utils.normalize_interface_label(interface_name)
        description = item.get("description")
        duplex = utils.normalize_interface_duplex(item.get("duplex"))
        speed = utils.normalize_interface_speed(item.get("bandwidth"))
        mac_address = (
            utils.normalize_mac_address(item.get("mac_address"))
            if not utils.incomplete_mac(item.get("mac_address"))
            else None
        )
        int_type = utils.normalize_interface_type(item.get("interface"))
        enabled = utils.normalize_interface_status(item.get("link_status"))
        mtu = utils.normalize_interface_mtu(item.get("mtu"))
        parent_name = utils.parent_interface(label)

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
            interface.create(**data)
        else:
            interface.update(interface_o, **data)

    # Update the log
    log.ingested = True
    log.save()
