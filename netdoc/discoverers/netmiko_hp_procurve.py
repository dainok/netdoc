"""Discovery task for HP Procurve devices via Netmiko."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import json
from nornir_utils.plugins.functions import print_result

from netdoc import utils
from netdoc.schemas import discoverable, discoverylog


def discovery(nrni, filters=None, filter_type=None):
    """Discovery HP Procurve devices."""
    # platform = "hp_procurve"
    host_list = []
    failed_host_list = []
    # Define commands, in order with command, template, enabled
    commands = [
        ("show system", "HOSTNAME"),
        ("show running-config", None),
        ("show interfaces brief", None),
        ("show vlans", None),
        ("show cdp neighbors detail", None),
        ("show lldp info remote-device", None),
        ("show mac-address", None),
        ("show arp", None),
        ("show trunks", None),
        ("show ip", None),
        ("show ip route", None),
        # Unsupported
        ("show version", None),
        ("show system", None),
        ("show logging", None),
        ("show spanning-tree", None),
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
    for multi_result in aggregated_results.values():
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
