"""Ingestor for json_vmware_vsphere_pyvmomi."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import (
    device,
    interface,
    virtualmachine,
    virtualmachine_interface,
    clustertype,
    cluster,
)
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    for host in log.parsed_output["hosts"].values():
        # Parsing hosts
        cluster_type = host.get("product_name")
        cluster_name = host.get("cluster_name")

        cluster_type_o = clustertype.get(cluster_type)
        if not cluster_type_o:
            cluster_type_o = clustertype.create(name=cluster_type)

        cluster_o = cluster.get(cluster_name)
        if not cluster_o:
            data_cluster = {
                "name": cluster_name,
                "type_id": cluster_type_o.id,
            }
            cluster_o = cluster.create(**data_cluster)

        data_host = {
            "name": utils.normalize_hostname(host.get("name")),
            "site_id": log.discoverable.site.id,
            "manufacturer_keyword": host.get("vendor"),
            "model_keyword": host.get("model"),
            "cluster_id": cluster_o.id,
        }
        device_o = device.get(name=data_host.get("name"))
        if not device_o:
            device_o = device.create(**data_host)
        else:
            device_o = device.update(device_o, **data_host)

        # Parsing host interfaces (vmNICs)
        for nic in host.get("nics").values():
            interface_name = nic.get("name")
            label = utils.normalize_interface_label(interface_name)
            mac_address = (
                utils.normalize_mac_address(nic.get("mac_address"))
                if not utils.incomplete_mac(nic.get("mac_address"))
                else None
            )
            int_type = utils.normalize_interface_type("vNIC")
            speed = (
                utils.normalize_interface_speed(f"{nic.get('speed')} MB/s")
                if nic.get("speed")
                else None
            )
            duplex = (
                utils.normalize_interface_duplex(str(nic.get("duplex")))
                if nic.get("duplex")
                else None
            )
            if speed:
                enabled = True
            data_vm_interface = {
                "name": interface_name,
                "mac_address": mac_address,
                "type": int_type,
                "device_id": device_o.id,
                "enabled": enabled,
                "speed": speed,
                "duplex": duplex,
            }
            interface_o = interface.get(device_id=device_o.id, label=label)
            if not interface_o:
                interface.create(**data_vm_interface)
            else:
                interface.update(interface_o, **data_vm_interface)

        # Parsing Virtual Machines
        for vm in host["vms"].values():  # pylint: disable=invalid-name
            # Get or create Device
            data_vm = {
                "name": utils.normalize_hostname(vm.get("name")),
                "device_id": device_o.id,
                "site_id": device_o.site.id,
                "cluster_id": device_o.cluster.id,
                "status": utils.normalize_vm_status(vm.get("power_state")),
                "vcpus": vm.get("vcpus"),
                "memory": vm.get("memory"),
                "disk": vm.get("total_disk_gb"),
            }
            vm_o = virtualmachine.get(name=data_vm.get("name"))
            if not vm_o:
                vm_o = virtualmachine.create(**data_vm)
            else:
                vm_o = virtualmachine.update(vm_o, **data_vm)

            # Parsing VM interfaces (vNICs)
            for nic in vm.get("nics"):
                interface_name = nic.get("label")
                mac_address = (
                    utils.normalize_mac_address(nic.get("mac_address"))
                    if not utils.incomplete_mac(nic.get("mac_address"))
                    else None
                )
                enabled = utils.normalize_interface_status(nic.get("connected"))

                data_vm_interface = {
                    "name": interface_name,
                    "mac_address": mac_address,
                    "virtual_machine_id": vm_o.id,
                    "enabled": enabled,
                }
                vm_interface_o = virtualmachine_interface.get(
                    virtual_machine_id=vm_o.id, name=interface_name
                )
                if not vm_interface_o:
                    virtualmachine_interface.create(**data_vm_interface)
                else:
                    virtualmachine_interface.update(vm_interface_o, **data_vm_interface)

    # Update the log
    log.ingested = True
    log.save()
