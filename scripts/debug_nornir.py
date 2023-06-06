"""Deep debug Nornir scripts."""
import logging
from pprint import pprint
from nornir import InitNornir
from nornir.core.filter import F
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir_netmiko.tasks import netmiko_send_command
from nornir_utils.plugins.functions import print_result

from netdoc.nornir_inventory import AssetInventory

ADDRESS = "172.25.82.34"
ENABLE = True
NORNIR_TIMEOUT = 120
COMMANDS = [
    "display current-configuration | include sysname",
    "display current-configuration",
    "display lldp neighbor-information verbose",
    "display lldp neighbor-information list",
    "display vlan brief",
    "display vlan all",
    "display ip vpn-instance",
    "display interface",
    "display ip interface",
    "display mac-address",
    "display link-aggregation verbose",
]

# Configuring Nornir
logger = logging.getLogger("nornir")
logger.setLevel(logging.DEBUG)
file_h = logging.FileHandler("nornir.log")
file_h.setLevel(logging.DEBUG)
logger.addHandler(file_h)

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
nrni = nrni.filter(F(hostname=ADDRESS))
pprint(nrni.inventory.dict())


# Tasks
def multiple_tasks(task):
    """Define commands (in order) for the playbook."""
    for command in COMMANDS:
        task.run(
            task=netmiko_send_command,
            name=command,
            command_string=command,
            use_textfsm=False,
            enable=ENABLE,
            use_timing=False,
            read_timeout=NORNIR_TIMEOUT,
        )


# Run the playbook
aggregated_results = nrni.run(task=multiple_tasks)

# Print the result
print_result(aggregated_results)
