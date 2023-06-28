"""Discovery task for VMware vSphere hosts via Python pyVmomi."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

import json
from nornir_utils.plugins.functions import print_result
from nornir.core.filter import F
from pyVmomi import vmodl, vim
from pyVmomi.VmomiSupport import VmomiJSONEncoder, templateOf
from pyVim.connect import SmartConnect

from netdoc import utils
from netdoc.schemas import discoverable, discoverylog


def api_query(
    details, host=None, username=None, password=None, verify_cert=True,
):  # pylint: disable=unused-argument
    """Get info via Python pyVmomi."""

    si = SmartConnect(host=host, user=username, pwd=password, disableSslCertValidation=not verify_cert)

    # Get VMs
    content = si.RetrieveContent()
    container = content.rootFolder  # starting point to look into
    view_type = [vim.VirtualMachine]  # object types to look for
    recursive = True  # whether we should look into it recursively
    container_view = content.viewManager.CreateContainerView(container, view_type, recursive)
    children = container_view.view

    data = []
    """
    	"net": [{
			"dynamicType": null,
			"dynamicProperty": [],
			"network": "VM Network",
			"ipAddress": ["172.25.82.108"],
			"macAddress": "00:0c:29:1f:2c:35",
			"connected": true,
			"deviceConfigId": 4000,
			"dnsConfig": null,
			"ipConfig": {
				"dynamicType": null,
				"dynamicProperty": [],
				"ipAddress": [{
					"dynamicType": null,
					"dynamicProperty": [],
					"ipAddress": "172.25.82.108",
					"prefixLength": 24,
					"origin": null,
					"state": "preferred",
					"lifetime": null,
					"_vimtype": "vim.net.IpConfigInfo.IpAddress"
				}],
				"dhcp": null,
				"autoConfigurationEnabled": null,
				"_vimtype": "vim.net.IpConfigInfo"
			},
			"netBIOSConfig": null,
			"_vimtype": "vim.vm.GuestInfo.NicInfo"
		}],
    """
    for child in children:
        # print(child)
        if child.name != "vCenter":
            continue
        vm_data = {
            "name": child.name,
            "guest": {
                "hostname": child.guest.hostName,
                "guest_address": child.guest.ipAddress,
            },
            "interfaces": [],
        }
        for network in child.guest.net:
            network_data = {
                "mac_address": network.macAddress,
                "connected": network.connected,
                "network": network.network,
                "ip_addresses": [],
            }
            for ip_address in network.ipConfig.ipAddress:
                network_data["ip_addresses"].append(F"{ip_address.ipAddress}/{ip_address.prefixLength}")

            vm_data["interfaces"].append(network_data)
        # data_vm = json.dumps(child, cls=VmomiJSONEncoder,
        #         # sort_keys=True,
        #         # explode=[
        #         #     templateOf('VirtualMachine'),
        #         # ]
        #     )
        # print(data_vm)
        print(vm_data)


    return data


def discovery(nrni):
    """Discovery Linux devices."""
    platform = "vmware_vsphere"
    host_list = []
    failed_host_list = []

    def multiple_tasks(task):
        """Define commands (in order) for the playbook."""
        supported = True
        order = 0
        template = None
        command = "aaa"
        verify_cert = task.host.dict().get("data").get("verify_cert")
        details = {
            "command": command,
            "template": template if template else command,
            "order": order,
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
    for key, multi_result in aggregated_results.items():
        current_nr = nrni.filter(F(name=key))

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
                raw_output=result.result,
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
