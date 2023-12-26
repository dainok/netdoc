"""Ingestor for netmiko_huawei_vrp_display_ip_vpn_instance_interface."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface, vrf, device
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device

    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/huawei_vrfp/display_ip_vpn-instance_interface # pylint: disable=line-too-long
        vrf_name = utils.normalize_vrf_name(item.get("name"))

        # Get or create VRF
        vrf_o = None
        if vrf_name:
            vrf_o = vrf.get_or_create(name=vrf_name)[0]

        for interface_name in item.get("interface_list"):
            label = utils.normalize_interface_label(interface_name)

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

    # Update management IP address
    device.update_management(device_o, log.discoverable.address)

    # Update the log
    log.ingested = True
    log.save()
