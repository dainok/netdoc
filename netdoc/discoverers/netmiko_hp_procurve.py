"""Discovery task for HP Procurve devices via Netmiko."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import json
from nornir_utils.plugins.functions import print_result

from netdoc import utils
from netdoc.schemas import discoverable, discoverylog


def discovery(nrni):
    """Discovery HP Procurve devices."""
    host_list = []
    failed_host_list = []

    def multiple_tasks(task):
        """Define commands (in order) for the playbook."""
        utils.append_nornir_netmiko_task(
            task, "show system", template="HOSTNAME", order=0
        )
        utils.append_nornir_netmiko_task(
            task,
            [
                "show running-config",
                "show interfaces brief",
                "show vlans",
                "show cdp neighbors detail",
                "show lldp info remote-device",
                "show mac-address",
                "show arp",
            ],
            order=10,
        )
        utils.append_nornir_netmiko_task(
            task,
            [
                "show trunks",
                "show ip",
                "show ip route",
            ],
        )
        utils.append_nornir_netmiko_task(
            task,
            [
                "show version",
                "show system",
                "show logging",
                "show spanning-tree",
            ],
            supported=False,
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
