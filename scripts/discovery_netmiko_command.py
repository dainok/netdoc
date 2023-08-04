"""Run discovery directly (without RQ).

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < run_discovery_command.py
"""

import json
import logging
import pprint
from slugify import slugify

from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir import InitNornir
from nornir.core.filter import F
from nornir_netmiko.tasks import netmiko_send_command

from netdoc.nornir_inventory import AssetInventory
from netdoc import utils
from netdoc.models import Discoverable

COMMANDS = [
    "show bgp ipv4 unicast",
]
FILTERS = list(
    Discoverable.objects.filter(discoverable=True, mode="netmiko_cisco_xr").values_list(
        "address", flat=True
    )
)

# Don't edit below this line


def main():
    """Main function."""
    # Configuring Nornir
    logger = logging.getLogger("nornir")
    logger.setLevel(logging.DEBUG)

    # Load Nornir custom inventory
    InventoryPluginRegister.register("asset-inventory", AssetInventory)

    # Create Nornir inventory
    nrni = InitNornir(
        runner={
            "plugin": "threaded",
            "options": {
                "num_workers": 100,
            },
        },
        inventory={"plugin": "asset-inventory"},
        logging={"enabled": False},
    )

    if FILTERS:
        # Execute on selected hosts only
        pprint.pprint(FILTERS)
        nrni = nrni.filter(F(hostname__in=FILTERS))

    def multiple_tasks(task):
        # Add commands to the playbook
        for command in COMMANDS:
            task.run(
                task=netmiko_send_command,
                name=command,
                command_string=command,
                use_textfsm=False,
                enable=False,
                use_timing=False,
            )

    # Run the playbook
    aggregated_results = nrni.run(task=multiple_tasks)

    # Save outputs and define additional commands
    for key, multi_result in aggregated_results.items():
        # MultiResult is an array of Result
        for result in multi_result:
            if result.name == "multiple_tasks":
                # Skip MultipleTask
                continue

            address = result.host.dict().get("hostname")
            discoverable_o = Discoverable.objects.get(address=address)
            raw_output = result.result
            platform = "_".join(discoverable_o.mode.split("_")[1:])
            command = result.name
            parsed_output, parsed = utils.parse_netmiko_output(
                result.result, command, platform
            )
            # Save to files
            filename = f"{address}-{platform}-{slugify(command)}"
            with open(filename + ".raw", "w") as fh:
                fh.write(raw_output)
            if parsed:
                with open(filename + ".json", "w") as fh:
                    json.dump(parsed_output, fh, indent=4, sort_keys=True)


if __name__ == "django.core.management.commands.shell":
    main()
