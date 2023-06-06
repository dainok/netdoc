"""Ingestor for netmiko_hp_comware_display_arp."""
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
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/hp_comware/display_arp # pylint: disable=line-too-long
        if utils.incomplete_mac(item.get("macaddress")):
            continue
        interface_name = item.get("interface")
        label = utils.normalize_interface_label(interface_name)
        ip_address = item.get("ipaddress")
        mac_address = utils.normalize_mac_address(item.get("macaddress"))

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
