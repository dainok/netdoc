"""Useful functions."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from os import path
import glob
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

from nornir_netmiko.tasks import netmiko_send_command
from netmiko.utilities import get_structured_data
from textfsm.parser import TextFSMError

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q

from core.models import Job
from extras.models import ScriptModule
from extras.scripts import run_script
from utilities.utils import NetBoxFakeRequest
from dcim.models import Interface
from virtualization.models import VMInterface


PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netdoc", {})


def append_nornir_netmiko_tasks(
    task, commands, enable=True, filters=None, filter_type=None, order=None
):
    """Apply filter to command lists and append to Nornir tasks."""
    if order is None:
        order = 0
    for command in commands:
        cmd_line = command[0]
        template = command[1] if command[1] else cmd_line

        if template == "HOSTNAME":
            # HOSTNAME is always included
            pass
        else:
            if is_command_filtered_out(cmd_line, filters, filter_type):
                # Command must be skipped
                continue

        # Append the command to Nornir tasks
        details = {
            "command": cmd_line,
            "template": template,
            "enable": enable,
            "order": order,
        }
        task.run(
            task=netmiko_send_command,
            name=json.dumps(details),
            command_string=details.get("command"),
            use_textfsm=False,
            enable=details.get("enable"),
            use_timing=False,
            read_timeout=PLUGIN_SETTINGS.get("NORNIR_TIMEOUT"),
        )
        order = order + 1


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
    virtual_interface_qs = VMInterface.objects.all()
    if sites:
        virtual_interface_qs = virtual_interface_qs.filter(
            virtual_machine__site_id__in=sites
        )
    if roles:
        virtual_interface_qs = virtual_interface_qs.filter(
            virtual_machine__role_id__in=roles
        )

    if mode == "l2":
        # Filter out Interface without cable
        interface_qs = interface_qs.exclude(cable__isnull=True)
        if vrfs:
            interface_qs = interface_qs.filter(ip_addresses__vrf_id__in=vrfs)
        # Not using virtual interfaces on L2 diagrams
        virtual_interface_qs = VMInterface.objects.none()
    elif mode == "l3":
        # Filter out Interface without IP address
        interface_qs = interface_qs.exclude(ip_addresses__isnull=True)
        virtual_interface_qs = virtual_interface_qs.exclude(ip_addresses__isnull=True)
        if include_global_vrf and not vrfs:
            # Include Global VRF only
            interface_qs = interface_qs.filter(ip_addresses__vrf__isnull=True)
            virtual_interface_qs = virtual_interface_qs.filter(
                ip_addresses__vrf__isnull=True
            )
        elif include_global_vrf and vrfs:
            # Include selected VRFs and Global VRF
            interface_qs = interface_qs.filter(
                Q(ip_addresses__vrf__isnull=True) | Q(ip_addresses__vrf_id__in=vrfs)
            )
            virtual_interface_qs = virtual_interface_qs.filter(
                Q(ip_addresses__vrf__isnull=True) | Q(ip_addresses__vrf_id__in=vrfs)
            )
        elif not include_global_vrf and vrfs:
            # Include selected VRFs only
            interface_qs = interface_qs.filter(ip_addresses__vrf_id__in=vrfs)
            virtual_interface_qs = virtual_interface_qs.filter(
                ip_addresses__vrf_id__in=vrfs
            )
    elif mode == "site":
        # Filter out Interface without cable
        interface_qs = interface_qs.exclude(cable__isnull=True)
        # Not using virtual interfaces on site diagrams
        virtual_interface_qs = VMInterface.objects.none()

    return list(interface_qs) + list(virtual_interface_qs)


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

    if port_description and "/" in port_description:
        # port_description contains /
        return normalize_interface_label(port_description)

    if port_id:
        # Give prevedence to port_id
        return normalize_interface_label(port_id)

    if port_description:
        # Use port_description
        return normalize_interface_label(port_description)

    # Invalid remote interface
    return None


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

    try:
        with open(library_file, "r", encoding="utf-8") as vendor_fh:
            # Load library file based on manufacturer
            data = yaml.safe_load(vendor_fh)
    except FileNotFoundError as exc:
        raise ValueError(
            f"manufacturer {manufacturer} not found in NetBox library"
        ) from exc

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


def find_vendor(keyword=None):
    """
    Get most similar Manufacturer (vendor) using Netbox devicetype-library.

    See: https://github.com/netbox-community/devicetype-library
    """
    netdoc_directory = path.dirname(path.realpath(__file__))
    library_file = f"{netdoc_directory}/library"

    files = glob.glob(f"{library_file}/*.yml")
    data = [path.basename(path.splitext(file)[0]) for file in files]
    data.sort()

    # Find closest words (part number/model)
    closests = get_close_matches(keyword, possibilities=data, n=1)

    if closests:
        # Found something
        return closests.pop()

    # othing found, try to lookup the first word only
    closests = get_close_matches(keyword.split(" ")[0], possibilities=data, n=1)

    if closests:
        # Found something
        return closests.pop()

    return None


def incomplete_mac(mac):
    """Return True if the MAC address is incomplete (from ARP table)."""
    if not mac:
        return True
    if "incomplete" in mac.lower().strip():
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


def is_command_supported(framework, platform, command):
    """Return true if the framework/platform/command is supported."""
    function_name = f"{framework}_{platform}_{command}"
    function_name = function_name.replace(" ", "_")
    function_name = function_name.replace("-", "_")
    function_name = function_name.lower().strip()
    try:
        importlib.import_module(f"netdoc.ingestors.{function_name}")
    except ModuleNotFoundError:
        # Ingestor not found
        return False
    return True


def is_command_filtered_out(cmd_line, filters, filter_type):
    """Test a command line against a filter and return True if the command must be skipped."""
    to_be_filtered = False
    if not filters:
        # No filter has been applied
        return False
    if filter_type == "exclude":
        # Exclude commands which match filter words (deny list)
        for keyword in filters:
            if keyword in cmd_line:
                # Mark command as skipped because matches the filter
                to_be_filtered = True
                break
    elif filter_type == "include":
        # Exclude commands which don't match filter words
        for keyword in filters:
            # Mark command as skipped by default
            to_be_filtered = True
            if keyword in cmd_line:
                # Include command
                to_be_filtered = False
                break
    else:
        # Filter type not valid
        raise ValueError(f"Filter type {filter_type} is not valid.")
    if to_be_filtered:
        # Skip commands marked as filtered
        return True
    return False


def log_ingest(log):
    """Ingest a log calling the custom ingestor."""
    function_name = (
        f"{log.details.get('framework')}_"
        + f"{log.details.get('platform')}_{log.template}"
    )
    function_name = function_name.replace(" ", "_")
    function_name = function_name.replace("-", "_")
    function_name = function_name.lower().strip()

    try:
        module = importlib.import_module(f"netdoc.ingestors.{function_name}")
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(f"Ingestor not found for {function_name}") from exc

    if log.order > 0 and not log.discoverable.device and not log.discoverable.vm:
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
        name = name.strip()  # Remove additional spaces
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
    duplex = duplex.lower().strip()
    if "auto" in duplex:
        return "auto"
    if "half" in duplex:
        return "half"
    if "full" in duplex:
        return "full"
    if "fd" in duplex:
        return "full"
    if "hd" in duplex:
        return "half"
    if "true" in duplex:
        return "auto"
    if "." == duplex:
        # Unkown (HPE Procurve)
        return None
    if "unknown" in duplex:
        # Unknown
        return None
    if "ukn" in duplex:
        # Unknown
        return None
    if "[n/a]" in duplex:
        # Unknown
        return None
    raise ValueError(f"Invalid duplex mode {duplex}")


def normalize_interface_label(name):
    """Given an interface name, return the shortname (label)."""
    name = name.lower().strip()
    if re.match(r".*-trk\d*$", name):
        # HPE Procurve add -Trk1 to interface port name
        name = re.sub(r"-trk\d*", "", name)

    if name.startswith("gigabitethernet"):
        return name.replace("gigabitethernet", "gi")
    if name.startswith("fastethernet"):
        return name.replace("fastethernet", "fa")
    if name.startswith("tengigabitethernet"):
        return name.replace("tengigabitethernet", "te")
    if name.startswith("ten-gigabitethernet"):  # HP Comware
        return name.replace("ten-gigabitethernet", "te")
    if name.startswith("xgigabitethernet"):  # Huawei
        return name.replace("xgigabitethernet", "te")
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
    if name.startswith("eth-trunk"):
        return name.replace("eth-trunk", "trunk")
    if name.startswith("eth"):
        return name.replace("eth", "e")
    if name.startswith("et"):
        return name.replace("et", "e")
    if name.startswith("vlanif"):  # Huawei
        return name.replace("vlanif", "vl")
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
    if name.startswith("bundle-ether"):
        # Cisco XR etherchannel
        return name.replace("bundle-ether", "be")
    if name.startswith("tengige"):
        # Cisco XR TenGigabitEthernet
        return name.replace("tengige", "te")
    if name.startswith("ge"):
        # HP Comware is using "gi" for GigabitEthernet, while Cisco is using "gi"
        return name.replace("ge", "gi")
    return name


def normalize_interface_mode(mode):
    """Normalize Interface mode (access/trunk/...)."""
    if not mode:
        # None is allowed
        return None
    mode = mode.lower().strip()
    if "trunk" in mode:
        return "tagged"
    if "hybrid" in mode:
        return "tagged"
    if "native-untagged" == mode:
        # HPE Aruba access port
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

    speed = speed.lower().strip()
    if "auto" in speed:
        # Speed is set to auto
        return None
    if "ukn" in speed:
        # Speed is unknown
        return None
    if "[n/a]" in speed:
        # Speed is unknown
        return None
    if "none" in speed:
        # Speed is unknown
        return None
    speed = speed.replace(" ", "")
    speed = speed.replace(".", "")
    speed = speed.replace("gigfd", "000")  # HP Procurve (000 is added from ingestor)
    speed = speed.replace("fdx", "")  # HP Procurve
    speed = speed.replace("fd", "")  # HP Procurve
    speed = speed.replace("hdx", "")  # HP Procurve
    speed = speed.replace("hd", "")  # HP Procurve
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
    if speed == 0:
        # Interfaces with speed 0 are down
        return None
    return speed


def normalize_interface_status(status):
    """Normalize interface status.

    Return True if the link is up, False elsewhere.
    """
    if status is None:
        # Assume None is used for virtual interfaces (e.g. tunnels)
        return True
    status = status.lower().strip()
    if "up" in status:
        return True
    if "true" in status:
        return True
    if "unknown" in status:
        # Assume unknown is used for virtual interfaces (e.g. tunnels)
        return True
    if "ukn" in status:
        # Paloalto unused HA interfaces
        return False
    if "down" in status:
        return False
    if "false" in status:
        return False
    if "disabled" in status:
        return False
    raise ValueError(f"Invalid interface status {status}")


def normalize_interface_type(name="", encapsulation=""):
    """Return interface type from name/encapsulation."""
    label = normalize_interface_label(name)
    encapsulation = encapsulation.lower().strip()
    if label == "sfp+sr":
        # HPE Procurve SPF
        return "other"
    if parent_interface(label):
        # Subinterface
        return "virtual"
    if re.match(r"^(po|bond).*", label):
        # LAG (portchannel, bond)
        return "lag"
    if label.startswith("lag"):
        # LAG (portchannel, bond)
        return "lag"
    if label.startswith("trunk"):
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


def normalize_rd(vrf_rd):
    """Return RD."""
    vrf_rd = vrf_rd.lower()
    vrf_rd = vrf_rd.strip()
    if not vrf_rd:
        return None
    if "not set" in vrf_rd:
        return None
    return vrf_rd


def normalize_route_type(route_type):
    """Return route type protocol."""
    route_type = route_type.lower().strip()
    if route_type in [
        "c",
        "connected",
        "direct",
        "local",
        "hsrp",
        "l",
        "a c",
        "a h",
        "a ~",
        "vrrp-engine",
        "vrrp_engine",
    ]:
        # Connected
        return "c"
    if route_type in ["s", "static", "s*", "a s"]:
        # Static
        return "s"
    if route_type in ["u", "hmm"]:
        # User-space Static
        return "u"
    if route_type in ["r", "a r"]:
        # RIP
        return "r"
    if route_type in ["b", "b*", "bgp", "a b", "a?b"]:
        # BGP
        return "b"
    if route_type in ["d"]:
        # EIGRP
        return "e"
    if route_type in ["ex"]:
        # EIGRP External
        return "ex"
    if route_type in ["o", "ospf", "a oi"]:
        # OSPF (Intra Area)
        return "o"
    if route_type in ["o", "ospf", "o_intra", "o ia", "a oo"]:
        # OSPF Inter Area
        return "oia"
    if route_type in ["n1", "o n1"]:
        # OSPF NSSA Type 1
        return "on1"
    if route_type in ["n2", "o n2"]:
        # OSPF NSSA Type 2
        return "on2"
    if route_type in ["o*e1", "e1", "o e1", "o_ase1", "a o1"]:
        # OSPF External Type 1
        return "oe1"
    if route_type in ["o*e2", "e2", "o e2", "o_ase2", "o_ase", "a o2"]:
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
    if re.match(r"^eigrp-\S+ internal$", route_type):
        # Nexus EIGRP with process
        return "e"
    if re.match(r"^eigrp-\S+ external$", route_type):
        # Nexus EIGRP External with process
        return "ex"
    if re.match(r"^ospf-\S+ intra$", route_type):
        # Nexus OSPF Inter Area with process
        return "oia"
    if re.match(r"^ospf-\S+ inter$", route_type):
        # Nexus OSPF Inter Area
        return "o"
    if re.match(r"^ospf-\S+ type-1$", route_type):
        # Nexus OSPF External Type 1 with process
        return "oe1"
    if re.match(r"^ospf-\S+ type-2$", route_type):
        # Nexus OSPF External Type 2 with process
        return "oe2"
    if re.match(r"^ospf-\S+ nssa type-1$", route_type):
        # Nexus OSPF NSSA Type 1 with process
        return "on1"
    if re.match(r"^ospf-\S+ nssa type-2$", route_type):
        # Nexus OSPF NSSA Type 2 with process
        return "on2"
    if re.match(r"^rip-\S+ rip$", route_type):
        # Nexus RIP with process
        return "r"
    if re.match(r"^bgp-\S+.*$", route_type):
        # Nexus BGP with process
        return "b"
    raise ValueError(f"Invalid route type {route_type}")


def normalize_serial(serial):
    """Serial number must be uppercase."""
    if serial:
        serial = serial.upper()
    return serial


def normalize_vm_status(status):
    """Status must be offline, active, planned, staged, failed, decomissioning."""
    status = status.lower().strip()
    if status in ["poweredon"]:
        # Active
        return "active"
    if status in ["poweredoff"]:
        # Offline
        return "offline"

    raise ValueError(f"Invalid virtual machine status {status}")


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

    vlan = vlan.lower().strip()
    vlan = vlan.replace("(default vlan)", "")
    vlan = vlan.replace(" ", "")
    if vlan in ["none", ""]:
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


def normalize_vrf_name(vrf_name):
    """Return VRF name."""
    if not vrf_name:
        # Empty VRF name means global VRF
        return None
    vrf_name = vrf_name.strip()
    if vrf_name == "default":
        # Default is global VRF
        return None
    if vrf_name.startswith("**"):
        # Special XR VRF
        return None
    return vrf_name


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
        if current_value is None or current_value == "":
            # Update only if not none
            setattr(obj, key, new_value)
            updated = True

    if updated:
        obj.save()
    return obj


def parent_interface(label, return_label=True):
    """If subinterface return parent interface else return None."""
    if return_label:
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


def spawn_script(script_name, get_data=None, post_data=None, file_list=None, user=None):
    """Spawn a Netbox Script defined into scripts folder and return the job_id."""
    if not get_data:
        get_data = {}
    if not post_data:
        post_data = {}
    if not file_list:
        file_list = {}
    if not user:
        user = User.objects.filter(is_superuser=True).order_by("pk")[0]

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

    # Inspired by ScriptView defined in extras/views.py
    module = ScriptModule.objects.get(file_path="netdoc_scripts.py")
    script = module.scripts[script_name]()
    job = Job.enqueue(
        run_script,
        instance=module,
        name=script.class_name,
        user=request.user,  # pylint: disable=no-member
        schedule_at=None,
        interval=None,
        job_timeout=script.job_timeout,
        data=request.POST,  # pylint: disable=no-member
        request=request,
    )

    return job.id
