"""Ingestor for netmiko_hp_comware_display_ip_interface."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface, device
from netdoc import utils


def ingest(log):
    """Processing parsed output.

    VRF - Interface association is ingested in the output of:
    "display ip vpn-instance instance-name <vrf>"
    """
    device_o = log.discoverable.device

    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/hp_comware/display_ip_interface # pylint: disable=line-too-long
        interface_name = item.get("intf")
        label = utils.normalize_interface_label(interface_name)
        ip_addresses = item.get("ipaddr")

        # Get or create Interface
        interface_o = interface.get(device_id=device_o.id, label=label)
        if not interface_o:
            interface_data = {
                "name": label,
                "device_id": device_o.id,
            }
            interface_o = interface.create(**interface_data)

        # Update Interface
        interface.update_addresses(interface_o, ip_addresses=ip_addresses)

    # Update management IP address
    device.update_management(device_o, log.discoverable.address)

    # Update the log
    log.ingested = True
    log.save()
