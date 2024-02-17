"""Ingestor for netmiko_allied_telesis_show_interface."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2024, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface, vrf
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device

    for item in log.parsed_output:
        if item.get("link_status") == "deleted":
            # Skip deleted interfaces
            continue
        interface_name = item.get("interface")
        label = utils.normalize_interface_label(interface_name)
        description = item.get("description")
        duplex = utils.normalize_interface_duplex(item.get("duplex"))
        mac_address = (
            utils.normalize_mac_address(item.get("mac_address"))
            if not utils.incomplete_mac(item.get("mac_address"))
            else None
        )
        int_type = utils.normalize_interface_type(item.get("interface"))
        enabled = utils.normalize_interface_status(item.get("protocol_status"))
        mtu = utils.normalize_interface_mtu(item.get("mtu"))
        parent_name = utils.parent_interface(label)
        ip_address = item.get("ip_address")
        mask = item.get("prefix_length")
        ip_addresses = [f"{ip_address}/{mask}"] if ip_address and mask else []
        vrf_name = item.get("vrf") if item.get("vrf") else None

        if parent_name:
            # Parent Interface is set
            parent_label = utils.normalize_interface_label(parent_name)
            parent_o = interface.get(device_id=device_o.id, label=parent_label)
            if not parent_o:
                parent_data = {
                    "name": parent_name,
                    "device_id": device_o.id,
                }
                parent_o = interface.create(**parent_data)

        # Get or create VRF
        vrf_o = None
        if vrf_name:
            vrf_o = vrf.get_or_create(name=vrf_name)[0]

        data = {
            "name": interface_name,
            "description": description,
            "duplex": duplex,
            "mac_address": mac_address,
            "type": int_type,
            "device_id": device_o.id,
            "enabled": enabled,
            "mtu": mtu,
            "parent_id": parent_o.id if parent_name else None,
            "vrf_id": vrf_o.id if vrf_o else None,
        }
        interface_o = interface.get(device_id=device_o.id, label=label)
        if not interface_o:
            interface_o = interface.create(**data)
        interface.update(interface_o, **data)
        interface.update_addresses(interface_o, ip_addresses=ip_addresses)

    # Update the log
    log.ingested = True
    log.save()
