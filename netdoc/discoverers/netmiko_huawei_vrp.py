"""Discovery task for Huawei VRP devices via Netmiko."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

import json
from nornir_utils.plugins.functions import print_result
from nornir.core.filter import F

from netdoc import utils
from netdoc.schemas import discoverable, discoverylog


def discovery(nrni, filters=None, filter_type=None):
    """Discovery Huawei VRP devices."""
    platform = "huawei_vrp"
    host_list = []
    failed_host_list = []
    # Define commands, in order with command, template, enabled
    commands = [
        ("display current-configuration | include sysname", "HOSTNAME"),
        ("display current-configuration", None),
        ("display device manufacture-info", None),
        ("display lldp neighbor", None),
        ("display ip vpn-instance", None),
        ("display interface", None),
        ("display ip vpn-instance interface", None),
        ("display eth-trunk", None),
        ("display ip interface", None),
        # Huawei shows VLAN name in display interface not in display vlan
        ("display vlan all", None),
        ("display lldp neighbor brief", None),
        ("display arp all", None),
        ("display mac-address", None),
    ]

    def multiple_tasks(task):
        """Define commands (in order) for the playbook."""
        utils.append_nornir_netmiko_tasks(
            task, commands, filters=filters, filter_type=filter_type
        )

    # Run the playbook
    aggregated_results = nrni.run(task=multiple_tasks)

    # Print the result
    print_result(aggregated_results)

    # Save outputs and define additional commands
    for key, multi_result in aggregated_results.items():
        vrfs = ["default"]  # Adding default VRF
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

            # Save VRF list for later
            if details.get("command") == "display ip vpn-instance":
                parsed_vrfs, parsed = utils.parse_netmiko_output(
                    result.result, details.get("command"), platform
                )
                if parsed:
                    for vrf in parsed_vrfs:
                        vrfs.append(vrf.get("name"))

        # Additional commands out of the multi result loop
        def additional_tasks(task):
            """Define additional commands (in order) for the playbook."""
            # Per VRF commands
            for vrf in vrfs:  # pylint: disable=cell-var-from-loop
                if vrf == "default":
                    # Default VRF has no name
                    commands = [("display ip routing-table verbose", None)]
                else:
                    # with non default VRF commands and templates differ
                    commands = [
                        (
                            f"display ip routing-table vpn-instance {vrf} verbose",
                            "display ip routing-table verbose",
                        ),
                    ]

                utils.append_nornir_netmiko_tasks(
                    task,
                    commands,
                    filters=filters,
                    filter_type=filter_type,
                    order=100,
                )

        # Run the additional playbook
        additional_aggregated_results = current_nr.run(task=additional_tasks)

        # Print the result
        print_result(additional_aggregated_results)

        for key, additional_multi_result in additional_aggregated_results.items():
            # MultiResult is an array of Result
            for result in additional_multi_result:
                if result.name == "additional_tasks":
                    # Skip MultipleTask
                    continue

                details = json.loads(result.name)
                if " vpn-instance " in details.get("command"):
                    # Save the VRF in details
                    vrf = details.get("command").split(" vpn-instance ").pop()
                    vrf = vrf.replace(" verbose", "")
                    details["vrf"] = vrf
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
