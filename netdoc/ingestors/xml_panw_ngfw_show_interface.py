"""Ingestor for xml_panw_ngfw_show_interface."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import (
    device,
    vrf,
    interface,
    virtualmachine_interface,
    virtualmachine,
)
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device if log.discoverable.device else None
    vm_o = log.discoverable.vm if log.discoverable.vm else None

    try:
        hardware_items = (
            log.parsed_output.get("response").get("result").get("hw").get("entry")
        )
    except AttributeError:
        hardware_items = []
    try:
        network_items = (
            log.parsed_output.get("response").get("result").get("ifnet").get("entry")
        )
    except AttributeError:
        network_items = []
    for item in hardware_items + network_items:
        physical = item.get("fwd") is None
        interface_name = item.get("name")
        label = utils.normalize_interface_label(interface_name)
        duplex = item.get("st").split("/")[1] if item.get("st") else None
        speed = f'{item.get("st").split("/")[0]}000' if item.get("st") else None
        mac_address = (
            utils.normalize_mac_address(item.get("mac"))
            if not utils.incomplete_mac(item.get("mac"))
            else None
        )
        int_type = utils.normalize_interface_type(item.get("name"))
        enabled = utils.normalize_interface_status(item.get("state"))
        vrf_name = utils.normalize_vrf_name(item.get("fwd"))
        if vrf_name:
            try:
                vrf_name = vrf_name.split(":")[1]
            except IndexError:
                vrf_name = None
        ip_addresses = []
        if item.get("ip") and item.get("ip") != "N/A":
            ip_addresses.append(item.get("ip"))

        # Get or create VRF
        vrf_o = None
        if vrf_name:
            vrf_o = vrf.get(name=vrf_name)
            if not vrf_o:
                data = {
                    "name": vrf_name,
                }
                vrf_o = vrf.create(**data)

        # Get or create Interface
        if vm_o:
            # Create a virtual interface
            parent_name = utils.parent_interface(interface_name, return_label=False)
            if parent_name:
                # Parent Interface is set
                parent_o = virtualmachine_interface.get(
                    virtual_machine_id=vm_o.id,
                    name=parent_name,
                )
                if not parent_o:
                    parent_data = {
                        "name": parent_name,
                        "virtual_machine_id": vm_o.id,
                    }
                    parent_o = virtualmachine_interface.create(**parent_data)

            interface_data = {
                "name": interface_name,
                "virtual_machine_id": vm_o.id,
                "mac_address": mac_address,
                "enabled": enabled,
                "parent_id": parent_o.id if parent_name else None,
                "vrf_id": vrf_o.id if vrf_o else None,
            }
            interface_o = virtualmachine_interface.get(
                virtual_machine_id=vm_o.id,
                name=interface_name,
            )
            if not interface_o:
                interface_o = virtualmachine_interface.create(**interface_data)
            virtualmachine_interface.update(interface_o, **interface_data)
            if not physical:
                virtualmachine_interface.update_addresses(
                    interface_o, ip_addresses=ip_addresses
                )

            # Update management IP address
            virtualmachine.update_management(vm_o, log.discoverable.address)
        if device_o:
            # Create a physical interface
            if parent_name:
                # Parent Interface is set
                parent_name = utils.parent_interface(interface_name)
                parent_label = utils.normalize_interface_label(parent_name)
                parent_o = interface.get(device_id=device_o.id, label=parent_label)
                if not parent_o:
                    parent_data = {
                        "name": parent_name,
                        "device_id": device_o.id,
                    }
                    parent_o = interface.create(**parent_data)

            interface_data = {
                "name": interface_name,
                "device_id": device_o.id,
                "duplex": duplex,
                "speed": speed,
                "mac_address": mac_address,
                "type": int_type,
                "enabled": enabled,
                "parent_id": parent_o.id if parent_name else None,
                "vrf_id": vrf_o.id if vrf_o else None,
            }
            interface_o = interface.get(device_id=device_o.id, label=label)
            if not interface_o:
                interface_o = interface.create(**interface_data)
            interface.update(interface_o, **interface_data)
            if not physical:
                interface.update_addresses(interface_o, ip_addresses=ip_addresses)

            # Update management IP address
            device.update_management(device_o, log.discoverable.address)

    # Update the log
    log.ingested = True
    log.save()
