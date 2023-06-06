"""Ingestor for netmiko_cisco_ios_show_ip_arp."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface, arptableentry
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device

    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/cisco_ios/show_ip_arp # pylint: disable=line-too-long
        if utils.incomplete_mac(item.get("mac")):
            continue
        interface_name = item.get("interface")
        label = utils.normalize_interface_label(interface_name)
        ip_address = item.get("address")
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
