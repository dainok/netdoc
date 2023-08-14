"""Discovery task for VMware vSphere hosts via Python pyVmomi."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

import json
import requests
from nornir_utils.plugins.functions import print_result

from django.conf import settings

from netdoc.schemas import discoverable, discoverylog

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netdoc", {})


def api_query(
    details,
    host_address=None,
    password=None,
    command=None,
    verify_cert=True,
):  # pylint: disable=unused-argument
    """Get info via Python request."""
    url = f"https://{host_address}:8444/api/?type=op&cmd={command}&key={password}"
    req = requests.get(url, verify=verify_cert, timeout=15)
    if req.status_code != 200:
        return f"ERROR CODE {req.status_code}\n{req.text}"
    return req.text


def append_nornir_task(
    task,
    command,
    template,
    order=128,
    host=None,
    password=None,
    supported=True,
    verify_cert=True,
):
    """Append a Nornir task within a multiple_tasks adding extended details."""
    details = {
        "command": command,
        "template": template,
        "enable": False,
        "order": order,
        "supported": supported,
    }
    task.run(
        task=api_query,
        name=json.dumps(details),
        command=details.get("command"),
        host_address=host,
        password=password,
        verify_cert=verify_cert,
    )


def discovery(nrni):
    """Discovery Palo Alto Networks NGFW devices."""
    host_list = []
    failed_host_list = []

    def multiple_tasks(task):
        """Define commands (in order) for the playbook."""
        params = {
            "host": task.host.hostname,
            "password": task.host.dict().get("password"),
            "verify_cert": task.host.dict().get("data").get("verify_cert"),
        }
        append_nornir_task(
            task,
            "<show><system><info></info></system></show>",
            template="show system info",
            order=0,
            **params,
        )
        append_nornir_task(
            task,
            "<show><interface>all</interface></show>",
            template="show interface",
            order=10,
            **params,
        )
        append_nornir_task(
            task,
            "<show><arp><entry name = 'all'/></arp></show>",
            template="show arp",
            **params,
        )
        append_nornir_task(
            task,
            "<show><mac>all</mac></show>",
            template="show mac",
            supported=False,
            **params,
        )
        append_nornir_task(
            task,
            "<show><vlan>all</vlan></show>",
            template="show vlan",
            supported=False,
            **params,
        )
        append_nornir_task(
            task,
            "<show><routing><route></route></routing></show>",
            template="show routing route",
            **params,
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
