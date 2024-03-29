"""Ingestor for netmiko_hp_procurve_show_lldp_info_remote_device."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface, device, cable
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device
    neighbors_per_interface = utils.count_interface_neighbors(
        log.parsed_output, "local_port"
    )

    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/hp_procurve/show_lldp_info_remote-device # pylint: disable=line-too-long
        local_interface_name = item.get("local_port")
        local_interface_label = utils.normalize_interface_label(local_interface_name)
        remote_name = utils.normalize_hostname(item.get("neighbor_sysname"))
        remote_interface_label = utils.get_remote_lldp_interface_label(
            port_id=item.get("neighbor_portid"),
            port_description=item.get("neighbor_descr"),
            system_description=None,
        )

        if not utils.is_hostname(remote_name):
            # Skip neighbors not announcing a valid hostname
            continue

        if not remote_interface_label:
            # Skip neighbors not announcing a valid interface
            continue

        if neighbors_per_interface.get(local_interface_label) > 1:
            # Skip interfaces with multiple neighbors
            continue

        if utils.parent_interface(local_interface_name) or utils.parent_interface(
            remote_interface_label
        ):
            # Skip subinterfaces
            continue

        # Get or create local Interface
        local_interface_o = interface.get(
            device_id=device_o.id, label=local_interface_label
        )
        if not local_interface_o:
            local_interface_data = {
                "name": local_interface_name,
                "device_id": device_o.id,
            }
            local_interface_o = interface.create(**local_interface_data)

        # Get or create remote Device
        remote_device_o = device.get(remote_name)
        if not remote_device_o:
            remote_device_data = {
                "name": remote_name,
                "site_id": device_o.site.id,
            }
            remote_device_o = device.create(**remote_device_data)

        # Get or create remote Interface
        remote_interface_o = interface.get(
            device_id=remote_device_o.id, label=remote_interface_label
        )
        if not remote_interface_o:
            remote_interface_data = {
                "name": remote_interface_label,
                "device_id": remote_device_o.id,
            }
            remote_interface_o = interface.create(**remote_interface_data)

        # Link
        cable.link(
            left_interface_id=local_interface_o.id,
            right_interface_id=remote_interface_o.id,
            protocol="lldp",
        )

    # Update the log
    log.ingested = True
    log.save()
