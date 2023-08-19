"""Ingestor for netmiko_hp_procurve_show_interfaces_brief."""
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
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/hp_procurve/show_interfaces_brief # pylint: disable=line-too-long
        interface_name = item.get("port")
        label = utils.normalize_interface_label(interface_name)
        duplex = utils.normalize_interface_duplex(item.get("mode"))
        speed = utils.normalize_interface_speed(f'{item.get("mode")}mbps')
        int_type = utils.normalize_interface_type(item.get("type"))
        enabled = (
            utils.normalize_interface_status(item.get("status"))
            if item.get("status")
            else None
        )
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
            "duplex": duplex,
            "speed": speed,
            "type": int_type,
            "device_id": device_o.id,
            "enabled": enabled,
            "parent_id": parent_o.id if parent_name else None,
        }

        interface_o = interface.get(device_id=device_o.id, label=label)
        if not interface_o:
            interface_o = interface.create(**data)
        else:
            interface_o = interface.update(interface_o, **data)

    # Update the log
    log.ingested = True
    log.save()
