"""Discovery task for HP Comware devices via Netmiko."""
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
    platform = "hp_comware"
    host_list = []
    failed_host_list = []
    # Define commands, in order with command, template, enabled
    commands = (
        [
            ("display current-configuration | include sysname", "HOSTNAME"),
            ("display current-configuration", None),
            # Depending on version, "verbose" may be unsupportted
            ("display lldp neighbor-information verbose", None),
            ("display lldp neighbor-information list", None),
            # Depending on version, "brief" may be unsupportted
            ("display vlan brief", None),
            ("display vlan all", None),
            ("display ip vpn-instance", None),
            ("display interface", None),
            ("display ip interface", None),
            ("display mac-address", None),
            ("display link-aggregation verbose", None),
            ("display_device_manuinfo", None),
            # Unsupported
            ("display version", None),
            ("display logbuffer level 6", None),
            ("display stp", None),
            ("display port trunk", None),
            ("display vrrp", None),
            ("display ospf peer", None),
            ("display bgp peer", None),
        ],
    )

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
                    commands = [
                        ("display arp", None),
                        ("display ip routing-table", None),
                    ]
                else:
                    # with non default VRF commands and templates differ
                    commands = [
                        (f"display arp vpn-instance {vrf}", "display arp"),
                        (
                            f"display ip vpn-instance instance-name {vrf}",
                            "display ip vpn-instance instance-name",
                        ),
                        (
                            f"display ip routing-table vpn-instance {vrf}",
                            "display ip routing-table",
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
                    details["vrf"] = (
                        details.get("command").split(" vpn-instance ").pop()
                    )
                elif " instance-name " in details.get("command"):
                    # Save the VRF in details
                    details["vrf"] = (
                        details.get("command").split(" instance-name ").pop()
                    )
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
