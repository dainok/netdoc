"""Ingestor for netmiko_allied_telesis_awplus_show_etherchannel_summary."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device

    for item in log.parsed_output:
        bundle_name = item.get("po_name")
        bundle_label = utils.normalize_interface_label(bundle_name)
        attached_interface_names = item.get("interfaces")

        # Get or create bundle Interface
        bundle_o = interface.get(device_id=device_o.id, label=bundle_label)
        if not bundle_o:
            bundle_data = {
                "name": bundle_name,
                "device_id": device_o.id,
            }
            bundle_o = interface.create(**bundle_data)
        # Set type on bundle Interface
        bundle_o = interface.update(bundle_o, type="lag")

        for attached_interface_name in attached_interface_names:
            # Get or create attached Interface
            attached_interface_label = utils.normalize_interface_label(
                attached_interface_name
            )
            attached_interface_o = interface.get(
                device_id=device_o.id, label=attached_interface_label
            )
            if not attached_interface_o:
                attached_interface_data = {
                    "name": attached_interface_name,
                    "device_id": device_o.id,
                }
                attached_interface_o = interface.create(**attached_interface_data)
            # Set LAG on attached Interface
            attached_interface_o = interface.update(
                attached_interface_o, lag_id=bundle_o.id
            )

    # Update the log
    log.ingested = True
    log.save()
