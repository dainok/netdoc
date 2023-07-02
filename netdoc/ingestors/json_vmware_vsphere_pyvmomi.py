"""Ingestor for json_vmware_vsphere_pyvmomi."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import device, interface
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    vendor = "VMware"

    # host -> vmnic/pnic -> physical switch
    # host -> vmnic/pnic -> (internal) -> vswitch/svswitch
    # vm -> vnic (porgroup name is the description) -> vswitch interface (+ portgroup vlanID)

    for host_id, host in log.parsed_output["hosts"].items():
        # Parsing Virtual Machines
        for vm_id, vm in host["vms"].items():
            # Get or create Device
            data = {
                "name": utils.normalize_hostname(vm.get("name")),
                "site_id": log.discoverable.site.id,
                "manufacturer": vendor,
            }
            device_o = device.get(name=data.get("name"))
            if not device_o:
                device_o = device.create(**data)

            # Parsing interfaces (vNICs)
            for nic in vm.get("nics"):
                interface_name = nic.get("label")
                label = utils.normalize_interface_label(interface_name)
                mac_address = (
                    utils.normalize_mac_address(nic.get("mac_address"))
                    if not utils.incomplete_mac(nic.get("mac_address"))
                    else None
                )
                int_type = utils.normalize_interface_type("vNIC")
                enabled = utils.normalize_interface_status(nic.get("connected"))

                data = {
                    "name": interface_name,
                    "mac_address": mac_address,
                    "type": int_type,
                    "device_id": device_o.id,
                    "enabled": enabled,
                }
                interface_o = interface.get(device_id=device_o.id, label=label)
                if not interface_o:
                    interface.create(**data)
                else:
                    interface.update(interface_o, **data)

    # Update the log
    log.ingested = True
    log.save()
