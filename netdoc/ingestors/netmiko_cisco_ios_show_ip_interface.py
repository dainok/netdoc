"""Ingestor for netmiko_cisco_ios_show_interfaces."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface, vrf, device
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device

    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/cisco_ios/show_ip_interface # pylint: disable=line-too-long
        if item.get("link_status") == "deleted":
            # Skip deleted interfaces
            continue
        interface_name = item.get("intf")
        label = utils.normalize_interface_label(interface_name)
        vrf_name = item.get("vrf")
        ip_list = item.get("ipaddr")
        mask_list = item.get("mask")
        ip_addresses = [
            f"{ipaddr}/{mask_list[index]}" for index, ipaddr in enumerate(ip_list)
        ]

        # Get or create VRF
        vrf_o = None
        if vrf_name:
            vrf_o = vrf.get(name=vrf_name)
            if not vrf_o:
                vrf_data = {
                    "name": vrf_name,
                }
                vrf_o = vrf.create(**vrf_data)

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
