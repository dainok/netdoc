"""Ingestor for xml_panw_ngfw_show_arp."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import (
    interface,
    virtualmachine_interface,
    arptableentry,
)
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device if log.discoverable.device else None
    vm_o = log.discoverable.vm if log.discoverable.vm else None

    try:
        items = (
            log.parsed_output.get("response").get("result").get("entries").get("entry")
        )
    except AttributeError:
        items = []
    for item in items:
        if utils.incomplete_mac(item.get("mac")):
            continue
        interface_name = item.get("interface")
        ip_address = item.get("ip")
        mac_address = utils.normalize_mac_address(item.get("mac"))

        if vm_o:
            # Get or create Interface
            interface_o = virtualmachine_interface.get(
                virtual_machine_id=vm_o.id,
                name=interface_name,
            )
            if not interface_o:
                interface_data = {
                    "name": interface_name,
                    "virtual_machine_id": vm_o.id,
                }
                interface_o = virtualmachine_interface.create(**interface_data)

            arptableentry_o = arptableentry.get(
                virtual_interface_id=interface_o.id,
                ip_address=ip_address,
                mac_address=mac_address,
            )
            if not arptableentry_o:
                data = {
                    "virtual_interface_id": interface_o.id,
                    "ip_address": ip_address,
                    "mac_address": mac_address,
                }
                arptableentry.create(**data)
        if device_o:
            # Get or create Interface
            interface_label = utils.normalize_interface_label(interface_name)
            interface_o = interface.get(device_id=device_o.id, label=interface_label)
            if not interface_o:
                interface_data = {
                    "name": interface_name,
                    "device_id": device_o.id,
                }
                interface_o = interface.create(**interface_data)

            arptableentry_o = arptableentry.get(
                interface_id=interface_o.id,
                ip_address=ip_address,
                mac_address=mac_address,
            )
            if not arptableentry_o:
                data = {
                    "interface_id": interface_o.id,
                    "ip_address": ip_address,
                    "mac_address": mac_address,
                }
                arptableentry.create(**data)

    # Update the log
    log.ingested = True
    log.save()
