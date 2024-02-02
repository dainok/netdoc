"""Discovery task for Cisco IOS devices via Netmiko."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import json
from nornir_utils.plugins.functions import print_result
from nornir.core.filter import F

from netdoc import utils
from netdoc.schemas import discoverable, discoverylog


def discovery(nrni, filters=None, filter_type=None):
    """Discovery Cisco IOS devices."""
    platform = "cisco_ios"
    host_list = []
    failed_host_list = []
    # Define commands, in order with command, template, enabled
    commands = [
        ("show version", "HOSTNAME"),
        ("show running-config", None),
        ("show vlan", None),
        ("show interfaces", None),
        ("show cdp neighbors detail", None),
        ("show lldp neighbors detail", None),
        ("show vrf", None),
        ("show ip interface", None),
        ("show mac address-table dynamic", "show mac address-table"),
        ("show etherchannel summary", None),
        ("show interfaces switchport", None),
        ("show inventory", None),
        # Unsupported
        ("show version", None),
        ("show logging", None),
        ("show spanning-tree", None),
        ("show interfaces trunk", None),
        ("show standby", None),
        ("show vrrp all", None),
        ("show glbp", None),
        ("show ip ospf neighbor", None),
        ("show ip eigrp neighbors", None),
        ("show ip bgp neighbors", None),
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
            if details.get("command").startswith("show vrf"):
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
                    commands = [
                        ("show ip arp", None),
                        ("show ip route connected", "show ip route"),
                        ("show ip route static", "show ip route"),
                        ("show ip route rip", "show ip route"),
                        ("show ip route bgp", "show ip route"),
                        ("show ip route eigrp", "show ip route"),
                        ("show ip route ospf", "show ip route"),
                        ("show ip route isis", "show ip route"),
                    ]
                else:
                    # with non default VRF commands and templates differ
                    commands = [
                        (f"show ip arp vrf {vrf}", "show ip arp"),
                        (f"show ip route vrf {vrf}", "show ip route"),
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
                if " vrf " in details.get("command"):
                    # Save the VRF in details
                    details["vrf"] = details.get("command").split(" vrf ").pop()
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
