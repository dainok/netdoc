"""Ingestor for json_vmware_vsphere_pyvmomi."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import device, interface
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    vendor = "VMware"

    # Parsing Virtual Machines
    for virtual_machine in log.parsed_output.get("virtual_machines"):
        # Get or create Device
        data = {
            "name": virtual_machine.get("name"),
            "site_id": log.discoverable.site.id,
            "manufacturer": vendor,
        }
        device_o = device.get(name=data.get("name"))
        if not device_o:
            device_o = device.create(**data)

        # Parsing interfaces (vNICs)
        for item in virtual_machine.get("interfaces"):
            interface_name = item.get("label")
            label = utils.normalize_interface_label(interface_name)
            mac_address = (
                utils.normalize_mac_address(item.get("mac_address"))
                if not utils.incomplete_mac(item.get("mac_address"))
                else None
            )
            int_type = utils.normalize_interface_type("vNIC")
            enabled = utils.normalize_interface_status(item.get("connected"))

            data = {
                "name": interface_name,
                "mac_address": mac_address,
                "type": int_type,
                "device_id": device_o.id,
                "enabled": enabled,
            }
            interface_o = interface.get(device_id=device_o.id, label=label)
            if not interface_o:
                interface.create(**data)
            else:
                interface.update(interface_o, **data)

    # Update the log
    log.ingested = True
    log.save()
