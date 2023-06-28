"""Discovery task for VMware vSphere hosts via Python pyVmomi."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

import json
from nornir_utils.plugins.functions import print_result
from pyVmomi import vim
from pyVim.connect import SmartConnect

from netdoc.schemas import discoverable, discoverylog


def api_query(
    details,
    host=None,
    username=None,
    password=None,
    verify_cert=True,
):  # pylint: disable=unused-argument
    """Get info via Python pyVmomi."""
    data = {
        "virtual_machines": [],
    }

    srv_inst = SmartConnect(
        host=host,
        user=username,
        pwd=password,
        disableSslCertValidation=not verify_cert,
    )
    content = srv_inst.RetrieveContent()
    container = content.rootFolder
    recursive = True

    # Get VMs
    view_type = [vim.VirtualMachine]  # pylint: disable=c-extension-no-member
    container_view = content.viewManager.CreateContainerView(
        container, view_type, recursive
    )
    for child in container_view.view:
        # For each VM
        # Get full attributes with:
        # from pyVmomi.VmomiSupport import VmomiJSONEncoder
        # dump = json.dumps(child, cls=VmomiJSONEncoder)
        # print(dump)
        vm_data = {
            "name": str(child.name),
            "summary": {
                "vm": str(child.summary.vm),
            },
            "runtime": {
                "host": str(child.runtime.host),
                "power_state": str(child.runtime.powerState),
            },
            "guest": {
                "hostname": str(child.guest.hostName),
                "guest_address": str(child.guest.ipAddress),
            },
            "config": {
                "guest_id": str(child.config.guestId),
                "guest_full_name": str(child.config.guestFullName),
            },
            "interfaces": [],
        }

        for network in child.guest.net:
            # For each network
            network_data = {
                "mac_address": str(network.macAddress),
                "connected": str(network.connected),
                "network": str(network.network),
                "ip_addresses": [],
            }
            if network.ipConfig:
                # Get network configuration if set (guest must be powered on)
                for ip_address in network.ipConfig.ipAddress:
                    network_data["ip_addresses"].append(
                        str(ip_address.ipAddress) + "/" + str(ip_address.prefixLength)
                    )

            # Save interface data
            vm_data["interfaces"].append(network_data)

        # Save VM data
        data["virtual_machines"].append(vm_data)

    return data


def discovery(nrni):
    """Discovery VMware vSphere devices."""
    host_list = []
    failed_host_list = []

    def multiple_tasks(task):
        """Define commands (in order) for the playbook."""
        supported = True
        order = 0
        template = None
        command = "pyVmomi"
        verify_cert = task.host.dict().get("data").get("verify_cert")
        details = {
            "command": command,
            "template": template if template else command,
            "order": order,
            "enable": False,
            "supported": supported,
            "verify_cert": verify_cert,
        }

        task.run(
            task=api_query,
            name=json.dumps(details),
            host=task.host.hostname,
            username=task.host.dict().get("username"),
            password=task.host.dict().get("password"),
            verify_cert=verify_cert,
        )

    # Run the playbook
    aggregated_results = nrni.run(task=multiple_tasks)

    # Print the result
    print_result(aggregated_results)

    # Save outputs and define additional commands
    for (
        key,  # pylint: disable=unused-variable
        multi_result,
    ) in aggregated_results.items():
        # MultiResult is an array of Result
        for result in multi_result:
            if result.name == "multiple_tasks":
                # Skip MultipleTask
                continue

            address = result.host.dict().get("hostname")
            discoverable_o = discoverable.get(address)
            details = json.loads(result.name)
            discoverylog.create(
                command=details.get("command"),
                discoverable_id=discoverable_o.id,
                raw_output=json.dumps(result.result),
                template=details.get("template"),
                order=details.get("order"),
                details=details,
            )

            # Tracking hosts and failed hosts
            if discoverable_o.address not in host_list:
                host_list.append(discoverable_o.address)
            if result.failed and discoverable_o.address not in failed_host_list:
                failed_host_list.append(discoverable_o.address)

    # Mark as discovered
    for address in host_list:
        if address not in failed_host_list:
            discoverable_o = discoverable.get(address, discovered=True)
            discoverable.update(discoverable_o)
