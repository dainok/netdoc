"""Useful functions."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from os import path
import re
import random
import importlib
import ipaddress
import string
import json
import uuid
from difflib import get_close_matches
import macaddress
import yaml
from yaml.loader import SafeLoader
from easysnmp import Session

from nornir_netmiko.tasks import netmiko_send_command
from netmiko.utilities import get_structured_data
from textfsm.parser import TextFSMError

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db.models import Q

from extras.scripts import get_scripts, run_script
from extras.models import JobResult, Script
from utilities.utils import NetBoxFakeRequest
from dcim.models import Interface


PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netdoc", {})
CONFIG_COMMANDS = [
    r"running-config",
    r"current-configuration",
]

FAILURE_OUTPUT = [
    # WARNING: must specify ^/\Z or a very unique string not found in valid outputs
    r"^$",  # Empty result
    r"^\s*Traceback",  # Python: traceback
    r"^\s*% Ambiguous command",  # Cisco: ambiguous command (command not supported)
    r"^\s*% Incomplete command",  # Cisco: incomplete command (command not supported)
    r"^\s*No link aggregation group exists",  # HP Comware: no port-channel configured
    r"^\s*% Unrecognized command found",  # HP Comware
    r"% \w+ is not enabled\s*\Z",  # Cisco: feature not enabled
    r"% \w+ not active\s*\Z",  # Cisco: feature not enabled
    r"% Wrong parameter found at",  # HP Comware
    r"% Unrecognized command found at",  # HP Comware
    r"% Invalid input detected at '\^' marker.\s*\Z",  # Cisco: invalid input detected
    r"% Invalid command at '\^' marker.\s*\Z",  # Cisco: invalid command detected
    r"No spanning tree instance exists.\s*\Z",  # Cisco STP
    r"No spanning tree instances exist.\s*\Z",  # Cisco STP
    r"Group\s+Port-channel\s+Protocol\s+Ports\s+[-+]+\s*\Z",  # Cisco etherchannel
    r"Group\s+Port-channel\s+Protocol\s+Ports\s+[-+]+\s*RU - L3",  # Cisco etherchannel
    r"Address\s+Age\s+MAC Address\s+Interface\s+Flags\s*\Z",  # Cisco ARP
    r"No VRF has been configured\s*\Z",  # Linux VRF
]

DRAWIO_ROLE_MAP = {
    "access-switch": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;shape=mxgraph.cisco19.rect;"
        + "prIcon=l2_switch;fillColor=#FAFAFA;strokeColor=#005073;",
        "width": 50,
        "height": 50,
    },
    "distribution-switch": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;shape=mxgraph.cisco19.rect;"
        + "prIcon=l3_switch;fillColor=#FAFAFA;strokeColor=#005073;",
        "width": 50,
        "height": 50,
    },
    "core-switch": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;shape=mxgraph.cisco19.rect;"
        + "prIcon=l3_modular;fillColor=#FAFAFA;strokeColor=#005073;",
        "width": 50,
        "height": 73,
    },
    "router": {
        "style": "sketch=0;points=[[0.5,0,0],[1,0.5,0],[0.5,1,0],[0,0.5,0],[0.145,0.145,0],"
        + "[0.8555,0.145,0],[0.855,0.8555,0],[0.145,0.855,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;shape=mxgraph.cisco19.rect;"
        + "prIcon=router;fillColor=#FAFAFA;strokeColor=#005073;",
        "width": 50,
        "height": 50,
    },
    "firewall": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;shape=mxgraph.cisco19.rect;"
        + "prIcon=firewall;fillColor=#FAFAFA;strokeColor=#005073;",
        "width": 64,
        "height": 50,
    },
    "server": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;"
        + "shape=mxgraph.cisco19.server;fillColor=#005073;strokeColor=none;",
        "width": 50,
        "height": 50,
    },
    "unknown": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;"
        + "shape=mxgraph.cisco19.server;fillColor=#005073;strokeColor=none;",
        "width": 27,
        "height": 50,
    },
}

SNMP_OID_MAP = {
    "sysName": "iso.3.6.1.2.1.1.5.0",
}


def append_nornir_netmiko_task(
    task, commands, enable=True, template=None, order=128, supported=True
):
    """Append a Nornir Netmiko task within a multiple_tasks adding extended details.

    commands can be str or list. template is allowed only if commands is str.
    """
    if isinstance(commands, str):
        commands = [commands]
    elif isinstance(commands, list) and template:
        raise ValueError("Cannot specify template for a list of commands")
    elif not isinstance(commands, list):
        raise ValueError("Command must be a string or a list of string")
    for command in commands:
        details = {
            "command": command,
            "template": template if template else command,
            "enable": enable,
            "order": order,
            "supported": supported,
        }
        for cmd_filter in PLUGIN_SETTINGS.get("NORNIR_SKIP_LIST"):
            if re.match(cmd_filter, command):
                # Skip excluded commands
                break
        else:
            # The filter does not match (filter loop completed successfully)
            task.run(
                task=netmiko_send_command,
                name=json.dumps(details),
                command_string=details.get("command"),
                use_textfsm=False,
                enable=details.get("enable"),
                use_timing=False,
                read_timeout=PLUGIN_SETTINGS.get("NORNIR_TIMEOUT"),
            )


def append_nornir_snmp_task(task, oids, template, order=128, supported=True):
    """Append a Nornir SNMP task within a multiple_tasks adding extended details.

    commands can be str or list of OIDs. template is allowed only if commands is str.
    """
    if isinstance(oids, str):
        oids = [oids]
    elif isinstance(oids, list) and template:
        raise ValueError("Cannot specify template for a list of OIDs")
    elif not isinstance(oids, list):
        raise ValueError("OID must be a string or a list of string")
    for oid in oids:
        details = {
            "command": oid,
            "template": template if template else oid,
            "enable": False,
            "order": order,
            "supported": supported,
        }
        for cmd_filter in PLUGIN_SETTINGS.get("NORNIR_SKIP_LIST"):
            if re.match(cmd_filter, oid):
                # Skip excluded commands
                break
        else:
            # The filter does not match (filter loop completed successfully)
            task.run(
                task=snmp_query,
                name=json.dumps(details),
                host=task.host.hostname,
                community=task.host.dict().get("data").get("snmp_community"),
                oid=oid,
            )


def count_interface_neighbors(neighbors_list, key):
    """Given a Netmiko parsed output, count CDP/LLDP neighbors per interface."""
    neighbors_per_interface = {}
    for item in neighbors_list:
        label = normalize_interface_label(item.get(key))
        if label not in neighbors_per_interface:
            neighbors_per_interface[label] = 0
        neighbors_per_interface[label] += 1
    return neighbors_per_interface


def delete_empty_keys(dct):
    """Delete None values recursively from a dictionary."""
    for key, value in list(dct.items()):
        if isinstance(value, dict):
            delete_empty_keys(value)
        elif value is None:
            del dct[key]
        elif isinstance(value, list):
            if not value:
                del dct[key]
            else:
                for v_i in value:
                    if isinstance(v_i, dict):
                        delete_empty_keys(v_i)
    return dct


def export_log(log):
    """Export DiscoveryLog in JSON format."""
    data = {
        "configuration": log.configuration,
        "details": log.details,
        "discoverable__mode": log.discoverable.mode,
        "ingested": log.ingested,
        "parsed": log.parsed,
        "parsed_output": log.parsed_output,
        "raw_output": log.raw_output,
        "success": log.success,
    }
    return data


def filter_keys(dct, allowed_keys):
    """Return a dict with only allowed keys."""
    filtered_dct = {}
    for key, value in dct.items():
        if key in allowed_keys:
            filtered_dct[key] = value
    return filtered_dct


def get_random_string(length):
    """Create a random lowercase string."""
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))  # nosec
    return result_str


def get_diagram_interfaces(
    mode, sites=None, roles=None, vrfs=None, include_global_vrf=False
):
    """Get relevant Interface queryset according to Diagram settings."""
    if not sites:
        sites = []
    if not roles:
        roles = []
    if not vrfs:
        vrfs = []

    interface_qs = Interface.objects.all()
    if sites:
        interface_qs = interface_qs.filter(device__site_id__in=sites)
    if roles:
        interface_qs = interface_qs.filter(device__device_role_id__in=roles)
    if mode == "l2":
        # Filter out Interface without cable
        interface_qs = interface_qs.exclude(cable__isnull=True)
        if vrfs:
            interface_qs = interface_qs.filter(ip_addresses__vrf_id__in=vrfs)
    if mode == "l3":
        # Filter out Interface without IP address
        interface_qs = interface_qs.exclude(ip_addresses__isnull=True)
        if include_global_vrf and not vrfs:
            # Include Global VRF only
            interface_qs = interface_qs.filter(ip_addresses__vrf__isnull=True)
        elif include_global_vrf and vrfs:
            # Include selected VRFs and Global VRF
            interface_qs = interface_qs.filter(
                Q(ip_addresses__vrf__isnull=True) | Q(ip_addresses__vrf_id__in=vrfs)
            )

        elif not include_global_vrf and vrfs:
            # Include selected VRFs only
            interface_qs = interface_qs.filter(ip_addresses__vrf_id__in=vrfs)

    return interface_qs


def get_remote_lldp_interface_label(
    port_id="", port_description="", system_description=""
):  # pylint: disable=unused-argument
    """
    Return the remote interface label.

    None is returned if no valid interface is found.
    The interface is selected based on port_id, port_description and system_description.
    The function tries to detect if port_id or port_description contain the interface description.
    """
    try:
        normalize_mac_address(port_id)
        # port_id contains a MAC address
        port_id = None
    except ValueError:
        pass

    try:
        normalize_mac_address(port_description)
        # port_description contains a MAC address
        port_description = None
    except ValueError:
        pass

    if port_id and re.match(r"\*\*\*|.*###|.*\[.*\]", port_id):
        # port_id contains a description
        port_id = None

    if port_description and re.match(r"\*\*\*|.*###|.*\[.*\]", port_description):
        # port_description contains a description
        port_description = None

    if port_id:
        # Give prevedence to port_id
        return normalize_interface_label(port_id)

    # Use port_description as last resort
    return normalize_interface_label(port_description)


def find_model(manufacturer=None, keyword=None):
    """
    Get most similar DeviceType (model) using Netbox devicetype-library.

    See: https://github.com/netbox-community/devicetype-library
    """
    if manufacturer == "Unknown":
        # Skip Unknown manufacturer
        return None

    netdoc_directory = path.dirname(path.realpath(__file__))
    library_file = f"{netdoc_directory}/library/{manufacturer}.yml"

    with open(library_file, "r", encoding="utf-8") as vendor_fh:
        # Load library file based on manufacturer
        data = yaml.load(vendor_fh, Loader=SafeLoader)

    # Find closest words (part number/model)
    closests = get_close_matches(keyword, possibilities=data.get("keywords"), n=1)
    if closests:
        # Found something
        closest = closests.pop()
        for item in data.get("models"):
            # Looking for the model based on closest word
            if item.get("model") == closest or item.get("part_number") == closest:
                return item

    return None


def incomplete_mac(mac):
    """Return True if the MAC address is incomplete (from ARP table)."""
    if not mac:
        return True
    if "incomplete" in mac.lower():
        return True
    return False


def is_hostname(name):
    """Return true if the hostname is valid."""
    if not name:
        # Hostname is empty
        return False
    allowed = re.compile(r"(?!-)[A-Z_\d-]{1,63}(?<!-)$", re.IGNORECASE)
    if all(allowed.match(x) for x in name.split(".")):
        return True
    # Hostname contains invalid chars
    return False


def log_ingest(log):
    """Ingest a log calling the custom ingestor."""
    function_name = f"{log.discoverable.mode}_{log.template}"
    function_name = function_name.replace(" ", "_")
    function_name = function_name.replace("-", "_")
    function_name = function_name.lower()

    try:
        module = importlib.import_module(f"netdoc.ingestors.{function_name}")
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(f"Ingestor not found for {function_name}") from exc

    if log.order > 0 and not log.discoverable.device:
        # Log with order > 0 must have a Device attached to the parent Discoverable
        raise ValueError(
            f"The discoverable {log.discoverable.address} does not have an attached device "
            + "thus logs cannot be ingested. Check if logs with priority 0 are ingested or if "
            + "Device is attached to a different Discoverable."
        )

    module.ingest(log)
    return log


def normalize_hostname(name):
    """Hostnames must be uppercase without domain."""
    if name:
        try:
            # Check if it's a valid IP Address
            ipaddress.ip_address(name)
            return name
        except ValueError:
            # Not a valid IP Address, it is a hostname
            pass
        name = name.split(".")[0]  # Removes domain if exists
        name = name.upper()
        name = re.sub(
            r"\(.+?\)", "", name
        )  # NX-OS: remove serial number (e.g. hostname(serialnumber))
    return name


def normalize_interface_duplex(duplex):
    """Normalize Interface.duplex."""
    if not duplex:
        # None is allowed
        return None
    duplex = duplex.lower()
    if "auto" in duplex:
        return "auto"
    if "half" in duplex:
        return "half"
    if "full" in duplex:
        return "full"
    if "unknown" in duplex:
        # Unknown
        return None
    raise ValueError(f"Invalid duplex mode {duplex}")


def normalize_interface_label(name):
    """Given an interface name, return the shortname (label)."""
    name = name.lower()
    if name.startswith("gigabitethernet"):
        return name.replace("gigabitethernet", "gi")
    if name.startswith("fastethernet"):
        return name.replace("fastethernet", "fa")
    if name.startswith("tengigabitethernet"):
        return name.replace("tengigabitethernet", "te")
    if name.startswith("ten-gigabitethernet"):  # HP Comware
        return name.replace("ten-gigabitethernet", "te")
    if name.startswith("m-gigabitethernet"):  # HP Comware
        return name.replace("m-gigabitethernet", "mge")
    if name.startswith("xge"):  # HP Comware
        return name.replace("xge", "te")
    if name.startswith("fortygige"):
        return name.replace("fortygige", "fge")
    if name.startswith("hundredgige"):
        return name.replace("hundredgige", "hge")
    if name.startswith("ethernet"):
        return name.replace("ethernet", "e")
    if name.startswith("eth"):
        return name.replace("eth", "e")
    if name.startswith("et"):
        return name.replace("et", "e")
    if name.startswith("vlan-interface"):  # HP Comware
        return name.replace("vlan-interface", "vl")
    if name.startswith("vlan"):
        return name.replace("vlan", "vl")
    if name.startswith("management"):
        return name.replace("management", "mgmt")
    if name.startswith("mgmteth0"):
        # Cisco XR Management interface
        return name.replace("mgmteth0", "mg0")
    if name.startswith("loopback"):
        return name.replace("loopback", "lo")
    if name.startswith("port-channel"):
        return name.replace("port-channel", "po")
    if name.startswith("route-aggregation"):
        return name.replace("route-aggregation", "ragg")
    if name.startswith("bridge-aggregation"):
        return name.replace("bridge-aggregation", "bagg")
    if name.startswith("tunnel"):
        return name.replace("tunnel", "tu")
    if name.startswith(
        "ge"
    ):  # HP Comware is using "gi" for GigabitEthernet, while Cisco is using "gi"
        return name.replace("ge", "gi")
    return name


def normalize_interface_mode(mode):
    """Normalize Interface mode (access/trunk/...)."""
    if not mode:
        # None is allowed
        return None
    mode = mode.lower()
    if "trunk" in mode:
        return "tagged"
    if "hybrid" in mode:
        return "tagged"
    if "access" in mode:
        return "access"
    if mode == "fex-fabric":
        # Cisco FEX
        return "tagged-all"
    if "private-vlan" in mode:
        # PVLAN still not supported by NetBox
        return None
    if "dot1q-tunnel" in mode:
        # QinQ still not supported by Netbox
        return None
    if "tunnel" in mode:
        # QinQ still not supported by Netbox
        return None
    if "dynamic auto" in mode:
        # dynamic state normally in shutdown so return none
        return None
    if "???" in mode:
        # Unknown mode
        return None
    if "down" in mode:
        # Ignore down interfaces
        return None
    raise ValueError(f"Invalid interface mode {mode}")


def normalize_interface_mtu(mtu):
    """
    Normalize MTU value returning an Interger.

    None is returned if mtu is empty or None.
    """
    if not mtu:
        # Return None if value is empty or None
        return None
    try:
        return int(mtu)
    except ValueError as exc:
        raise ValueError(f"Invalid MTU {mtu}") from exc


def normalize_interface_speed(speed):
    """Normalize Interface speed in kb/s."""
    if not speed:
        # None is allowed
        return None

    speed = speed.lower()
    if "auto" in speed:
        # Speed is set to auto
        return None
    speed = speed.replace(" ", "")
    speed = speed.replace("kbit", "")
    speed = speed.replace("kbps", "")
    speed = speed.replace("mbps", "000")
    speed = speed.replace("mb/s", "000")
    speed = speed.replace("gb/s", "000000")
    speed = speed.replace("gbps", "000000")
    try:
        speed = int(speed)
    except ValueError as exc:
        raise ValueError(f"Invalid interface speed {speed}") from exc
    return speed


def normalize_interface_status(status):
    """Normalize interface status.

    Return True if the link is up, False elsewhere.
    """
    status = status.lower()
    if "up" in status:
        return True
    if "down" in status:
        return False
    if "disabled" in status:
        return False
    raise ValueError(f"Invalid interface status {status}")


def normalize_interface_type(name="", encapsulation=""):
    """Return interface type from name/encapsulation."""
    label = normalize_interface_label(name)
    encapsulation = encapsulation.lower()
    if parent_interface(label):
        # Subinterface
        return "virtual"
    if re.match(r"^(po|bond).*", label):
        # LAG (portchannel, bond)
        return "lag"
    if re.match(r"lo.*", label):
        # Loopback
        return "virtual"
    if re.match(r"tun.*", label):
        # Tunnel
        return "virtual"
    if re.match(r"vl.*", label):
        # SVI (VLAN interface)
        return "bridge"
    if re.match(r"null.*", label):
        # Null
        return "virtual"
    if "loopback" in encapsulation:
        # Loopback
        return "virtual"
    if "tunnel" in encapsulation:
        # Tunnel
        return "virtual"
    # If not found return "other"
    return "other"


def normalize_mac_address(mac_address):
    """Return a MAC Address in the format 01:23:45:67:89:AB."""
    if not mac_address:
        # Convert None in empty string to raise ValueError only
        mac_address = ""

    # Removing non hex chars
    mac_address = mac_address.replace("-", "")
    mac_address = mac_address.replace(":", "")
    # Converting into a MAC object (as a validator)
    mac_address_o = macaddress.MAC(mac_address)
    # Return the MAC address in Netbox format
    return str(mac_address_o).replace("-", ":")


def normalize_ip_address_or_none(ip_address):
    """
    Return IP address (10.1.2.3) or None from string.

    String can be 10.1.2.3 or 10.1.2.3/24.
    """
    try:
        # 10.1.2.3
        ip_address_o = ipaddress.ip_address(ip_address)
        return str(ip_address_o)
    except ValueError:
        pass

    try:
        # 10.1.2.3/24
        ip_network_o = ipaddress.ip_interface(ip_address)
        return str(ip_network_o.ip)
    except ValueError:
        pass

    return None


def normalize_route_type(route_type):
    """Return route type protocol."""
    route_type = route_type.lower()
    if route_type in ["c", "direct", "local", "hsrp", "l"]:
        # Connected
        return "c"
    if route_type in ["s", "static", "s*"]:
        # Static
        return "s"
    if route_type in ["u"]:
        # User-space Static
        return "u"
    if route_type in ["r", "rip-10"]:
        # RIP
        return "r"
    if route_type in ["b", "bgp"]:
        # BGP
        return "b"
    if route_type in ["d"]:
        # EIGRP
        return "e"
    if route_type in ["ex"]:
        # EIGRP External
        return "ex"
    if route_type in ["o", "ospf", "o_intra", "o ia"]:
        # OSPF Inter Area
        return "oia"
    if route_type in ["n1", "o n1"]:
        # OSPF NSSA Type 1
        return "on1"
    if route_type in ["n2", "o n2"]:
        # OSPF NSSA Type 2
        return "on2"
    if route_type in ["e1", "o e1", "o_ase1"]:
        # OSPF External Type 1
        return "oe1"
    if route_type in ["e2", "o e2", "o_ase2", "o_ase"]:
        # OSPF External Type 2
        return "oe2"
    if route_type in ["i"]:
        # IS-IS
        return "i"
    if route_type in ["su"]:
        # IS-IS Summary
        return "is"
    if route_type in ["l1"]:
        # IS-IS L1
        return "i1"
    if route_type in ["l2"]:
        # IS-IS
        return "i2"
    if route_type in ["unknown"]:
        # Unknown
        return "u"
    if re.match(r"^ospf-\S+ intra$", route_type):
        # Nexus OSPF Inter Area with process
        return "oia"

    raise ValueError(f"Invalid route type {route_type}")


def normalize_serial(serial):
    """Serial number must be uppercase."""
    if serial:
        serial = serial.upper()
    return serial


def normalize_vlan_list(trunking_vlans):
    """Normalize a VLAN list (can be a comma separated string or a list)."""
    vlans = []
    if isinstance(trunking_vlans, list):
        for vlan in trunking_vlans:
            vlans.extend(normalize_vlan_range(vlan))
    else:
        vlans.extend(normalize_vlan_range(trunking_vlans))
    return vlans


def normalize_vlan_range(vlan):
    """Normalize a single VLAN or VLAN range, returning a list of integer."""
    if isinstance(vlan, int):
        # Integer
        return [vlan]

    vlan = vlan.lower()
    vlan = vlan.replace("(default vlan)", "")
    vlan = vlan.replace(" ", "")
    if vlan == "none":
        return []
    if vlan == "all":
        # All VLANs
        return normalize_vlan_range("1-4094")
    if "," in vlan:
        # Set of VLANs (must before VLAN range)
        vlans = []
        for value in vlan.split(","):
            vlans.extend(normalize_vlan_range(value))
        return vlans
    if "-" in vlan:
        # VLAN range
        try:
            return list(range(int(vlan.split("-")[0]), int(vlan.split("-")[1]) + 1))
        except ValueError as exc:
            raise ValueError(f"cannot convert VLAN {vlan} range to integer") from exc
    try:
        return [int(vlan)]
    except ValueError as exc:
        raise ValueError(f"cannot convert VLAN {vlan} to integer") from exc


def object_create(model_o, **kwargs):
    """Create a generic Model object using kwargs."""
    return model_o.objects.create(**kwargs)


def object_get_or_none(model_o, **kwargs):
    """Get a generic Model object using kwargs. None is returned if not found."""
    try:
        return model_o.objects.get(**kwargs)
    except model_o.DoesNotExist:
        return None


def object_list(model_o, **kwargs):
    """Get a list of Model objects."""
    result = model_o.objects.filter(**kwargs)
    return list(result)


def object_update(obj, force=True, **kwargs):
    """Update a generic Model object using kwargs. Object is saved only if modified.

    With force=False, the field is updated only if not set.
    """
    updated = False
    for key, new_value in kwargs.items():
        current_value = getattr(obj, key)
        if new_value == current_value:
            # No need to update
            continue
        if force:
            # Always update
            setattr(obj, key, new_value)
            updated = True
        if current_value is None:
            # Update only if not none
            setattr(obj, key, new_value)
            updated = True

    if updated:
        obj.save()
    return obj


def parent_interface(label):
    """If subinterface return parent interface else return None."""
    label = normalize_interface_label(label)
    if re.match(r"^[^.]+\.[0-9]+$", label):
        # Contains only one "." and ends with numbers
        parent_label = re.sub(r".[0-9]+$", "", label)
        return parent_label
    if re.match(r"^[^+]+\+\S+$", label):
        # Contains only one "+" and ends with alphanumeric
        # Cisco "service instance" Ethernet
        parent_label = re.sub(r"\+\S+$", "", label)
        return parent_label
    return None


def parse_netmiko_output(output, command, platform, template=None):
    """Parse Netmiko output using NTC templates."""
    if not template:
        # If template is empty, use command as template
        template = command
    if template == "HOSTNAME":
        # Parsed during ingestion
        return output, True
    try:
        parsed_output = get_structured_data(output, platform=platform, command=template)
        if isinstance(parsed_output, str) and parsed_output == output:
            # NTC template not found
            return (
                "Output not parsed, check if NTC template exists and debug it.",
                False,
            )
        if not isinstance(parsed_output, dict) and not isinstance(parsed_output, list):
            parsed_output = f"Not a valid dict or list\n\n{parsed_output}"
            return parsed_output, False
        return parsed_output, True
    except TextFSMError as exc:
        return str(exc), False


def snmp_query(
    details, host=None, community=None, oid=None
):  # pylint: disable=unused-argument
    """Get info via SNMP."""
    # TODO: support also for tables
    session = Session(hostname=host, community=community, version=2)
    sysname = session.get(SNMP_OID_MAP.get(oid))
    return sysname.value


def spawn_script(script_name, get_data=None, post_data=None, file_list=None, user=None):
    """Spawn a Netbox Script defined into scripts folder."""
    if not get_data:
        get_data = {}
    if not post_data:
        post_data = {}
    if not file_list:
        file_list = {}
    if not user:
        user = User.objects.filter(is_superuser=True).order_by("pk")[0]

    script = get_scripts().get("NetDoc").get(script_name)
    request = NetBoxFakeRequest(
        {
            "META": {},
            "POST": post_data,
            "GET": get_data,
            "FILES": file_list,
            "user": user,
            "id": uuid.uuid4(),
        }
    )

    JobResult.enqueue_job(
        run_script,
        name=script.full_name,
        obj_type=ContentType.objects.get_for_model(Script),
        user=request.user,  # pylint: disable=no-member
        schedule_at=None,
        interval=None,
        job_timeout=script.job_timeout,
        data=request.POST,  # pylint: disable=no-member
        request=request,
    )
