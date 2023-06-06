"""Discovery task for Cisco NX-OS devices via Netmiko."""
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
    """Discovery Cisco NX-OS devices."""
    platform = "cisco_nxos"
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
                "show interface",
                "show cdp neighbors detail",
                "show lldp neighbors detail",
                "show vlan",
                "show vrf",
            ],
            order=10,
        )
        utils.append_nornir_netmiko_task(
            task, "show mac address-table dynamic", template="show mac address-table"
        )
        utils.append_nornir_netmiko_task(
            task,
            [
                "show ip route vrf all",
                "show port-channel summary",
                "show interface switchport",
                "show inventory",
            ],
        )
        utils.append_nornir_netmiko_task(
            task,
            [
                "show version",
                "show logging",
                "show spanning-tree",
                "show interface trunk",
                "show vpc",
                "show vdc",
                "show hsrp all",
                "show vrrp",
                "show glbp",
                "show ip ospf neighbor",
                "show ip eigrp neighbors",
                "show ip bgp neighbors",
            ],
            supported=False,
        )

    # Run the playbook
    aggregated_results = filtered_devices.run(task=multiple_tasks)

    # Print the result
    print_result(aggregated_results)

    # Save outputs and define additional commands
    for key, multi_result in aggregated_results.items():
        vrfs = []
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
                        vrfs.append(vrf.get("name"))

        # Additional commands out of the multi result loop
        def additional_tasks(task):
            """Define additional commands (in order) for the playbook."""
            # Per VRF commands
            for vrf in vrfs:  # pylint: disable=cell-var-from-loop
                utils.append_nornir_netmiko_task(
                    task,
                    commands=f"show ip interface vrf {vrf}",
                    template="show ip interface",
                )
                utils.append_nornir_netmiko_task(
                    task,
                    commands=f"show ip arp vrf {vrf}",
                    template="show ip arp",
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
