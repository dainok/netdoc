"""Discovery task for Cisco XR devices via Netmiko."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import json
from nornir_utils.plugins.functions import print_result
from nornir.core.filter import F

from netdoc import utils
from netdoc.schemas import discoverable, discoverylog


def discovery(nrni):
    """Discovery Cisco XR devices."""
    platform = "cisco_xr"
    filtered_devices = nrni.filter(platform=platform)

    def multiple_tasks(task):
        """Define commands (in order) for the playbook."""
        utils.append_nornir_netmiko_task(
            task, "show running-config | include hostname", template="HOSTNAME", order=0
        )
        utils.append_nornir_netmiko_task(
            task,
            [
                "show running-config",
                "show interfaces",
                "show cdp neighbors detail",
                "show lldp neighbors",
                "show vrf all detail",
                "show ipv4 interface",
                "admin show inventory",
            ],
            order=10,
        )
        utils.append_nornir_netmiko_task(
            task,
            [
                "show inventory",
            ],
        )
        utils.append_nornir_netmiko_task(
            task,
            [
                "show hsrp",
                "show vrrp",
                "show ospf neighbor",
                "show eigrp neighbors",
                "show bgp neighbors",
            ],
            supported=False,
        )

    # Run the playbook
    aggregated_results = filtered_devices.run(task=multiple_tasks)

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
            discoverable_o = discoverable.get(address, discovered=True)
            details = json.loads(result.name)
            discoverylog.create(
                command=details.get("command"),
                discoverable_id=discoverable_o.id,
                raw_output=result.result,
                template=details.get("template"),
                order=details.get("order"),
                details=details,
            )

            # Save VRF list for later
            if details.get("command") == "show vrf":
                parsed_vrfs, parsed = utils.parse_netmiko_output(
                    result.result, details.get("command"), platform
                )
                if parsed:
                    for vrf in parsed_vrfs:
                        vrfs.append(vrf.get("vrf"))

        # Additional commands out of the multi result loop
        def additional_tasks(task):
            """Define additional commands (in order) for the playbook."""
            # Per VRF commands
            for vrf in vrfs:  # pylint: disable=cell-var-from-loop
                if vrf == "default":
                    # Default VRF has no name
                    utils.append_nornir_netmiko_task(
                        task,
                        [
                            "show arp",
                        ],
                    )
                    utils.append_nornir_netmiko_task(
                        task,
                        commands="show route connected",
                        template="show route",
                    )
                    utils.append_nornir_netmiko_task(
                        task,
                        commands="show route static",
                        template="show route",
                    )
                    utils.append_nornir_netmiko_task(
                        task,
                        commands="show route rip",
                        template="show route",
                    )
                    utils.append_nornir_netmiko_task(
                        task,
                        commands="show route bgp",
                        template="show route",
                    )
                    utils.append_nornir_netmiko_task(
                        task,
                        commands="show route eigrp",
                        template="show route",
                    )
                    utils.append_nornir_netmiko_task(
                        task,
                        commands="show route ospf",
                        template="show route",
                    )
                    utils.append_nornir_netmiko_task(
                        task,
                        commands="show route isis",
                        template="show route",
                    )
                else:
                    # with non default VRF commands and templates differ
                    utils.append_nornir_netmiko_task(
                        task, commands=f"show arp vrf {vrf}", template="show ip arp"
                    )
                    utils.append_nornir_netmiko_task(
                        task,
                        commands=f"show route vrf {vrf}",
                        template="show route",
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
