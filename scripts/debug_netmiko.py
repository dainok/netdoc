"""Deep debug Netmiko scripts."""
import logging
from netmiko import ConnectHandler

from netdoc import models

ADDRESS = "172.25.82.34"
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

# Don't edit below this line

logging.basicConfig(filename="netmiko_global.log", level=logging.DEBUG)
logger = logging.getLogger("netmiko")

discoverable_o = models.Discoverable.objects.get(address=ADDRESS)
device = {
    "device_type": discoverable_o.mode.replace("netmiko_", ""),
    "host": discoverable_o.address,
    "username": discoverable_o.credential.username,
    "password": discoverable_o.credential.password,
    "session_log": "netmiko_session.log",
}

net_connect = ConnectHandler(**device)
for command in COMMANDS:
    net_connect.send_command(command)
net_connect.disconnect()
