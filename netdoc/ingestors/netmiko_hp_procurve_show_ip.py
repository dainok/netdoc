"""Ingestor for netmiko_hp_procurve_show_ip."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

import ipaddress

from netdoc.schemas import interface, device
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device

    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/hp_procurve/show_ip # pylint: disable=line-too-long
        if not item.get("ip_address"):
            # Skip interfaces without IP address
            continue
        interface_name = item.get("vlan_name")
        label = utils.normalize_interface_label(interface_name)
        ip_address = item.get("ip_address")
        ip_address = (
            str(
                ipaddress.IPv4Interface(
                    f"{item.get('ip_address')}/{item.get('subnet_mask')}"
                )
            )
            if item.get("ip_address")
            else None
        )

        # Get or create Interface
        interface_o = interface.get(device_id=device_o.id, label=label)
        if not interface_o:
            interface_data = {
                "name": label,
                "device_id": device_o.id,
                "type": "other",
            }
            interface_o = interface.create(**interface_data)

        # Update Interface
        if ip_address:
            interface.update_addresses(interface_o, ip_addresses=[ip_address])

            # Update management IP address
            device.update_management(device_o, log.discoverable.address)

    # Update the log
    log.ingested = True
    log.save()
