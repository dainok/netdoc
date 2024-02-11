"""Ingestor for netmiko_allied_teresis_show_ip_interface."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2024, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface, device
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device
    vrf_o = None

    for item in log.parsed_output:
        if item.get("link_status") == "deleted":
            # Skip deleted interfaces
            continue
        interface_name = item.get("intf")
        label = utils.normalize_interface_label(interface_name)
        #        vrf_name = item.get("vrf")
        ip_list = item.get("ipaddr")
        mask_list = item.get("mask")
        ip_addresses = [
            f"{ipaddr}/{mask_list[index]}" for index, ipaddr in enumerate(ip_list)
        ]

        # Get or create Interface
        interface_o = interface.get(device_id=device_o.id, label=label)
        if not interface_o:
            interface_data = {
                "name": label,
                "device_id": device_o.id,
            }
            interface_o = interface.create(**interface_data)

        # Update Interface
        data = {
            "vrf_id": vrf_o.id if vrf_o else None,
        }
        interface.update(interface_o, **data)
        interface.update_addresses(interface_o, ip_addresses=ip_addresses)

    # Update management IP address
    device.update_management(device_o, log.discoverable.address)

    # Update the log
    log.ingested = True
    log.save()
