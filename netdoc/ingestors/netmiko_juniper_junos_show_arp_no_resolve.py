"""Ingestor for netmiko_juniper_junos_show_arp_no_resolve."""
__author__ = "Andy Brown"
__contact__ = "andy@thebmwz3.co.uk"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface, arptableentry
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device

    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/juniper_junos/show_arp_no-resolve # pylint: disable=line-too-long
        if utils.incomplete_mac(item.get("mac")):
            continue
        interface_name = item.get("interface")
        label = utils.normalize_interface_label(interface_name)
        ip_address = item.get("ip_address")
        mac_address = utils.normalize_mac_address(item.get("mac"))

        interface_o = interface.get(device_id=device_o.id, label=label)
        if not interface_o:
            interface_data = {
                "name": label,
                "device_id": device_o.id,
            }
            interface_o = interface.create(**interface_data)

        arptableentry_o = arptableentry.get(
            interface_id=interface_o.id, ip_address=ip_address, mac_address=mac_address
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