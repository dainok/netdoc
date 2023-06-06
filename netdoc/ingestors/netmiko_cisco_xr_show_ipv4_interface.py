"""Ingestor for netmiko_cisco_xr_show_ipv4_interface."""
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
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/cisco_xr/show_ipv4_interface # pylint: disable=line-too-long
        interface_name = item.get("interface")
        label = utils.normalize_interface_label(interface_name)
        vrf_name = item.get("vrf")
        ip_address = item.get("ip_address") if item.get("ip_address") else None
        ip_addresses = [ip_address]

        # Get or create VRF
        vrf_o = None
        if vrf_name and vrf_name != "default":
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
