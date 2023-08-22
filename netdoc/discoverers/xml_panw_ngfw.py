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
from netdoc import utils

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netdoc", {})


def api_query(
    details,
    host_address=None,
    password=None,
    command=None,
    verify_cert=True,
):  # pylint: disable=unused-argument
    """Get info via Python request."""
    url = f"https://{host_address}/api/?type=op&cmd={command}&key={password}"
    req = requests.get(url, verify=verify_cert, timeout=15)
    if req.status_code != 200:
        return f"ERROR CODE {req.status_code}\n{req.text}"
    return req.text


def append_nornir_tasks(
    task,
    commands,
    filters=None,
    filter_type=None,
    order=None,
    host=None,
    password=None,
    supported=True,
    verify_cert=True,
):
    """Append a Nornir tasks within a multiple_tasks adding extended details."""
    if order is None:
        order = 0

    for command in commands:
        cmd_line = command[0]
        template = command[1]

        if template == "show system info":
            # HOSTNAME is always included
            pass
        else:
            if utils.is_command_filtered_out(template, filters, filter_type):
                # Command must be skipped
                continue

        # Append the command to Nornir tasks
        details = {
            "command": cmd_line,
            "template": template,
            "enable": False,
            "order": order,
            "supported": supported,
        }
        task.run(
            task=api_query,
            name=json.dumps(details),
            command=cmd_line,
            host_address=host,
            password=password,
            verify_cert=verify_cert,
        )
        order = order + 1


def discovery(nrni, filters=None, filter_type=None):
    """Discovery Palo Alto Networks NGFW devices."""
    host_list = []
    failed_host_list = []
    # Define commands, in order with command, template
    commands = [
        ("<show><system><info></info></system></show>", "show system info"),
        ("<show><interface>all</interface></show>", "show interface"),
        ("<show><arp><entry name = 'all'/></arp></show>", "show arp"),
        ("<show><mac>all</mac></show>", "show mac"),
        ("<show><vlan>all</vlan></show>", "show vlan"),
        ("<show><routing><route></route></routing></show>", "show routing route"),
    ]

    def multiple_tasks(task):
        """Define commands (in order) for the playbook."""
        params = {
            "host": task.host.hostname,
            "password": task.host.dict().get("password"),
            "verify_cert": task.host.dict().get("data").get("verify_cert"),
        }
        append_nornir_tasks(
            task,
            commands,
            filters=filters,
            filter_type=filter_type,
            **params,
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
