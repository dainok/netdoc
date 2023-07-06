"""Ingestor for json_vmware_vsphere_pyvmomi."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import device, interface, virtualmachine
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    vendor = "VMware"

    # host -> vmnic/pnic -> physical switch
    # host -> vmnic/pnic -> (internal) -> vswitch/svswitch
    # vm -> vnic (porgroup name is the description) -> vswitch interface (+ portgroup vlanID)

    for host_id, host in log.parsed_output["hosts"].items():
        # Parsing hosts
        data_host = {
            "name": utils.normalize_hostname(host.get("name")),
            "site_id": log.discoverable.site.id,
            "manufacturer_keyword": host.get("vendor"),
            "model_keyword": host.get("model"),
        }
        device_o = device.get(name=data_host.get("name"))
        if not device_o:
            device_o = device.create(**data_host)

        # Parsing host interfaces (vmNICs)
        # for nic in vm.get("nics"):
        #     interface_name = nic.get("name")
        #     label = utils.normalize_interface_label(interface_name)
        #     mac_address = (
        #         utils.normalize_mac_address(nic.get("mac_address"))
        #         if not utils.incomplete_mac(nic.get("mac_address"))
        #         else None
        #     )
        #     int_type = utils.normalize_interface_type("vNIC")
        #     # enabled = utils.normalize_interface_status(nic.get("connected"))
        #     # TODO

        #     data_vm_interface = {
        #         "name": interface_name,
        #         "mac_address": mac_address,
        #         "type": int_type,
        #         "device_id": device_o.id,
        #         # "enabled": enabled,
        #     }
        #     interface_o = interface.get(device_id=device_o.id, label=label)
        #     if not interface_o:
        #         interface.create(**data_vm_interface)
        #     else:
        #         interface.update(interface_o, **data_vm_interface)


        # Parsing Virtual Machines
        for vm_id, vm in host["vms"].items():
            # Get or create Device
            data_vm = {
                "name": utils.normalize_hostname(vm.get("name")),
                "device_id": device_o.id,
                "site_id": device_o.site.id,
                "cluster_id": device_o.cluster.id,
                "status": utils.normalize_vm_status(vm.get("power_state")),
            }
            vm_o = virtualmachine.get(name=data_vm.get("name"))
            if not vm_o:
                vm_o = virtualmachine.create(**data_vm)

            # # Parsing VM interfaces (vNICs)
            # for nic in vm.get("nics"):
            #     interface_name = nic.get("label")
            #     label = utils.normalize_interface_label(interface_name)
            #     mac_address = (
            #         utils.normalize_mac_address(nic.get("mac_address"))
            #         if not utils.incomplete_mac(nic.get("mac_address"))
            #         else None
            #     )
            #     int_type = utils.normalize_interface_type("vNIC")
            #     enabled = utils.normalize_interface_status(nic.get("connected"))

            #     data_vm_interface = {
            #         "name": interface_name,
            #         "mac_address": mac_address,
            #         "type": int_type,
            #         "device_id": device_o.id,
            #         "enabled": enabled,
            #     }
            #     interface_o = interface.get(device_id=device_o.id, label=label)
            #     if not interface_o:
            #         interface.create(**data_vm_interface)
            #     else:
            #         interface.update(interface_o, **data_vm_interface)

    # Update the log
    log.ingested = True
    log.save()
