"""Ingestor for xml_panw_ngfw_show_system_info."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import device, virtualmachine
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    # See https://github.com/netbox-community/devicetype-library/tree/master/device-types # pylint: disable=line-too-long
    vendor = "Palo Alto"

    # Getting data
    name = log.parsed_output.get("response").get("result").get("system").get("devicename")
    model = log.parsed_output.get("response").get("result").get("system").get("model")
    family = log.parsed_output.get("response").get("result").get("system").get("family")
    serial = log.parsed_output.get("response").get("result").get("system").get("serial")
    ip_address = log.parsed_output.get("response").get("result").get("system").get("ip-address")
    netmask = log.parsed_output.get("response").get("result").get("system").get("netmask")

    # Parsing data
    name = utils.normalize_hostname(name)
    virtual = True if family == "vm" else False

    if virtual:
        # Get or create VM
        data = {
            "name": name,
            "site_id": log.discoverable.site.id,
            "status": "active",
        }
        vm_o = virtualmachine.get(name=data.get("name"))
        if not vm_o:
            vm_o = virtualmachine.create(**data)
    else:
        # Get or create Device
        data = {
            "name": name,
            "site_id": log.discoverable.site.id,
            "manufacturer": vendor,
        }
        device_o = device.get(name=data.get("name"))
        if not device_o:
            device_o = device.create(**data)

        # Update device
        device.update(
            device_o,
            serial=serial,
            manufacturer=vendor,
            model_keyword=model,
        )

    # Update the log
    log.ingested = True
    log.save()
