"""Discovery task for VMware vSphere hosts via Python pyVmomi."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

import json
import requests
from nornir_utils.plugins.functions import print_result

from netdoc.schemas import discoverable, discoverylog


def api_query(
    details,
    host_address=None,
    password=None,
    command=None,
    verify_cert=True,
):  # pylint: disable=unused-argument
    """Get info via Python request."""
    url = (
        f"https://{host_address}:8444/api/?type=op&cmd={command}&key={password}"
    )
    req = requests.get(url, verify=verify_cert, timeout=15)
    if req.status_code != 200:
        return f"ERROR CODE {req.status_code}\n" + req.text
    # PANOS API misses XML version header
    return f'<?xml version="1.0"?>\n{req.text}'
                    

def discovery(nrni):
    """Discovery Palo Alto Networks NGFW devices."""
    host_list = []
    failed_host_list = []

    def multiple_tasks(task):
        """Define commands (in order) for the playbook."""
        supported = True
        order = 0
        template = "show arp"
        command = "<show><arp><entry name = 'all'/></arp></show>"
        verify_cert = task.host.dict().get("data").get("verify_cert")
        # TODO: <show><mac></mac></show>
        # TODO: <show><interface></interface></show>
        # TODO: <show><routing><route></route></routing></show>
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
            command=command,
            host_address=task.host.hostname,
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
