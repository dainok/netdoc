"""Ingestor for json_vmware_vsphere_pyvmomi."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import re

from netdoc.schemas import device, discoverable
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    vendor = "VMware"
    name = log.parsed_output

    # Parsing Virtual Machines
    for virtual_machine in log.parsed_output.get("virtual_machines"):
        # Get or create Device
        data = {
            "name": virtual_machine.get("name"),
            "site_id": log.discoverable.site.id,
            "manufacturer": vendor,
        }
        device_o = device.get(name=data.get("name"))
        if not device_o:
            device_o = device.create(**data)

    # Update the log
    log.ingested = True
    log.save()