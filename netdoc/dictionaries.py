"""Dictionaries.

Group all dictionaries used in NetDoc.
"""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

from utilities.choices import ChoiceSet


CONFIG_COMMANDS = [
    # Commands including a device configuration
    r"running-config",
    r"current-configuration",
]


CREDENTIAL_ENCRYPTED_FIELDS = [
    # Fields encrypted in Discoverable
    "password",
    "enable_password",
]


DRAWIO_ROLE_MAP = {
    # Stencil attributes used when exporting diagrams in Draw.io format
    "access-switch": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;shape=mxgraph.cisco19.rect;"
        + "prIcon=l2_switch;fillColor=#FAFAFA;strokeColor=#005073;",
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
    "distribution-switch": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;shape=mxgraph.cisco19.rect;"
        + "prIcon=l3_switch;fillColor=#FAFAFA;strokeColor=#005073;",
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
    "handled": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;"
        + "shape=mxgraph.cisco19.handheld;fillColor=#005073;strokeColor=none;",
        "width": 37,
        "height": 50,
    },
    "laptop": {
        "style": "points=[[0.13,0.02,0],[0.5,0,0],[0.87,0.02,0],[0.885,0.4,0],[0.985,0.985,0],"
        + "[0.5,1,0],[0.015,0.985,0],[0.115,0.4,0]];verticalLabelPosition=bottom;sketch=0;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;"
        + "shape=mxgraph.cisco19.laptop;fillColor=#005073;strokeColor=none;",
        "width": 50,
        "height": 35,
    },
    "load-balancer": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;shape=mxgraph.cisco19.rect;"
        + "prIcon=load_balancer;fillColor=#FAFAFA;strokeColor=#005073;",
        "width": 64,
        "height": 50,
    },
    "router": {
        "style": "sketch=0;points=[[0.5,0,0],[1,0.5,0],[0.5,1,0],[0,0.5,0],[0.145,0.145,0],"
        + "[0.8555,0.145,0],[0.855,0.8555,0],[0.145,0.855,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;shape=mxgraph.cisco19.rect;"
        + "prIcon=router;fillColor=#FAFAFA;strokeColor=#005073;",
        "width": 50,
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
    "site": {
        "style": "points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[1,0.25,0],[1,0.5,0],"
        + "[1,0.75,0],[1,1,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],[0,1,0],[0,0.75,0],[0,0.5,0],"
        + "[0,0.25,0]];verticalLabelPosition=bottom;sketch=0;html=1;verticalAlign=top;"
        + "aspect=fixed;align=center;pointerEvents=1;shape=mxgraph.cisco19.branch;"
        + "fillColor=#005073;strokeColor=none;",
        "width": 50,
        "height": 50,
    },
    "storage": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;"
        + "shape=mxgraph.cisco19.rect;prIcon=storage;fillColor=#FAFAFA;strokeColor=#005073;",
        "width": 64,
        "height": 50,
    },
    "unknown": {
        "style": "sketch=0;points=[[0.5,0,0],[1,0.5,0],[0.5,1,0],[0,0.5,0],[0.145,0.145,0],"
        + "[0.8555,0.145,0],[0.855,0.8555,0],[0.145,0.855,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;"
        + "shape=mxgraph.cisco19.lock;fillColor=#005073;strokeColor=none;",
        "width": 50,
        "height": 50,
    },
    "virtual-switch": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;shape=mxgraph.cisco19.rect;"
        + "prIcon=nexus_1k;fillColor=#FAFAFA;strokeColor=#005073;",
        "width": 64,
        "height": 50,
    },
    "wireless-ap": {
        "style": "points=[[0.03,0.36,0],[0.18,0,0],[0.5,0.34,0],[0.82,0,0],[0.97,0.36,0],"
        + "[1,0.67,0],[0.975,0.975,0],[0.5,1,0],[0.025,0.975,0],[0,0.67,0]];"
        + "verticalLabelPosition=bottom;sketch=0;html=1;verticalAlign=top;aspect=fixed;"
        + "align=center;pointerEvents=1;shape=mxgraph.cisco19.wireless_access_point;"
        + "fillColor=#005073;strokeColor=none;",
        "width": 50,
        "height": 50,
    },
    "wireless-controller": {
        "style": "sketch=0;points=[[0.015,0.015,0],[0.985,0.015,0],[0.985,0.985,0],[0.015,0.985,0],"
        + "[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0.25,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],"
        + "[0.25,1,0],[0,0.75,0],[0,0.5,0],[0,0.25,0]];verticalLabelPosition=bottom;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;shape=mxgraph.cisco19.rect;"
        + "prIcon=wireless_lan_controller;fillColor=#FAFAFA;strokeColor=#005073;",
        "width": 64,
        "height": 50,
    },
    "workstation": {
        "style": "points=[[0.03,0.03,0],[0.5,0,0],[0.97,0.03,0],[1,0.4,0],[0.97,0.745,0],[0.5,1,0],"
        + "[0.03,0.745,0],[0,0.4,0]];verticalLabelPosition=bottom;sketch=0;html=1;"
        + "verticalAlign=top;aspect=fixed;align=center;pointerEvents=1;"
        + "shape=mxgraph.cisco19.workstation;fillColor=#005073;strokeColor=none;",
        "width": 50,
        "height": 40,
    },
}


FAILURE_OUTPUT = [
    # Regex used to declare a command execution failed
    # WARNING: must specify ^/\Z or a very unique string not found in valid outputs
    r"^$",  # Empty result
    r"^\s*.?Traceback",  # Python: traceback
    r"^\s*% Ambiguous command",  # Cisco: ambiguous command (command not supported)
    r"^\s*% Incomplete command",  # Cisco: incomplete command (command not supported)
    r"^\s*No link aggregation group exists",  # HP Comware: no port-channel configured
    r"^\s*% Unrecognized command found",  # HP Comware
    r"% \w+ is not enabled\s*\Z",  # Cisco: feature not enabled
    r"% \w+ not active\s*\Z",  # Cisco: feature not enabled
    r"% No matching routes found",  # Cisco XR
    r"% BGP instance '\w' not active",  # Cisco XR
    r"% LLDP is not enabled",  # Cisco XR
    r"% Wrong parameter found at",  # HP Comware
    r"% Unrecognized command found at",  # HP Comware
    r"% Invalid input detected at '\^' marker.\s*\Z",  # Cisco: invalid input detected
    r"% Invalid command at '\^' marker.\s*\Z",  # Cisco: invalid command detected
    r"No spanning tree instance exists.\s*\Z",  # Cisco STP
    r"No spanning tree instances exist.\s*\Z",  # Cisco STP
    r"Group\s+Port-channel\s+Protocol\s+Ports\s+[-+]+\s*\Z",  # Cisco etherchannel
    r"Group\s+Port-channel\s+Protocol\s+Ports\s+[-+]+\s*RU - L3\Z",  # Cisco etherchannel
    r"Address\s+Age\s+MAC Address\s+Interface\s+Flags\s*\Z",  # Cisco ARP
    r"No VRF has been configured\s*\Z",  # Linux VRF
    r"No records found\s*\Z",  # HP Procurve CDP
    r"^\s*\S+\s+\S+\s+\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2}\.\d{1,3}\s+\S+\s*\Z",  # Cisco timestamp
    r"Gateway of last resort is not set\s*\Z",  # Cisco IOS empty routing table
    r"Gateway of last resort is \d+\.\d+\.\d+\.\d+ to network \d+\.\d+\.\d+\.\d+\s*\Z",
    r"^\s*% VRF \S+ does not exist",  # Cisco invalid VRF
    r"^\s*% IP routing table vrf \S+ does not exist",  # Cisco invalid VRF
    r"^\s*No LAG configured.",  # HPE Aruba
    r"^ERROR CODE \d+",  # HTTP requests
]


class DeviceImageChoices(ChoiceSet):
    """Image used in diagrams associated to device roles."""

    CHOICES = [
        ("access-switch", "Access Switch"),
        ("core-switch", "Core Switch"),
        ("distribution-switch", "Distribution Switch"),
        ("firewall", "Firewall"),
        ("laptop", "Laptop"),
        ("load-balancer", "Load Balancer"),
        ("mobile", "Mobile device"),
        ("router", "Router"),
        ("server", "Server"),
        ("storage", "Storage"),
        ("unknown", "Unknown"),
        ("virtual-switch", "Virtual Switch"),
        ("wireless-ap", "Wireless AP"),
        ("wireless-controller", "Wireless Controller"),
        ("workstation", "Workstation"),
    ]


class DiagramModeChoices(ChoiceSet):
    """Diagram mode."""

    CHOICES = [
        ("l2", "L2"),
        ("l3", "L3"),
        ("site", "Site connections"),
        # ("stp", "STP"),
    ]


class DiscoveryModeChoices(ChoiceSet):
    """Discovey mode."""

    MODES = {
        "netmiko_aruba_aoscx": {
            "name": "Netmiko Aruba OSCX",
            "platform": "aruba_osswitch",  # Netmiko type, used by Nornir
            "protocol": "ssh",
            "framework": "netmiko",
            "discovery_script": "netmiko_aruba_oscx",  # Discovery script called by tasks.py
        },
        "netmiko_cisco_ios": {
            "name": "Netmiko Cisco IOS XE",
            "platform": "cisco_ios",  # Netmiko type, used by Nornir
            "protocol": "ssh",
            "framework": "netmiko",
            "discovery_script": "netmiko_cisco_ios",  # Discovery script called by tasks.py
        },
        "netmiko_cisco_ios_telnet": {
            "name": "Netmiko Cisco IOS XE (Telnet)",
            "platform": "cisco_ios_telnet",  # Netmiko type, used by Nornir
            "protocol": "telnet",
            "framework": "netmiko",
            "discovery_script": "netmiko_cisco_ios",  # Discovery script called by tasks.py
        },
        "netmiko_cisco_nxos": {
            "name": "Netmiko Cisco NX-OS",
            "platform": "cisco_nxos",  # Netmiko type, used by Nornir
            "protocol": "ssh",
            "framework": "netmiko",
            "discovery_script": "netmiko_cisco_nxos",  # Discovery script called by tasks.py
        },
        "netmiko_cisco_xr": {
            "name": "Netmiko Cisco XR",
            "platform": "cisco_xr",  # Netmiko type, used by Nornir
            "protocol": "ssh",
            "framework": "netmiko",
            "discovery_script": "netmiko_cisco_xr",  # Discovery script called by tasks.py
        },
        "netmiko_hp_comware": {
            "name": "Netmiko HPE Comware",
            "platform": "hp_comware",  # Netmiko type, used by Nornir
            "protocol": "ssh",
            "framework": "netmiko",
            "discovery_script": "netmiko_hp_comware",  # Discovery script called by tasks.py
        },
        "netmiko_hp_procurve": {
            "name": "Netmiko HPE Procurve",
            "platform": "hp_procurve",  # Netmiko type, used by Nornir
            "protocol": "ssh",
            "framework": "netmiko",
            "discovery_script": "netmiko_hp_procurve",  # Discovery script called by tasks.py
        },
        "netmiko_hp_procurve_telnet": {
            "name": "Netmiko HPE Procurve (Telnet)",
            "platform": "hp_procurve_telnet",  # Netmiko type, used by Nornir
            "protocol": "telnet",
            "framework": "netmiko",
            "discovery_script": "netmiko_hp_procurve",  # Discovery script called by tasks.py
        },
        "netmiko_huawei_vrp": {
            "name": "Netmiko Huawei VRP",
            "platform": "huawei",  # Netmiko type, used by Nornir
            "protocol": "ssh",
            "framework": "netmiko",
            "discovery_script": "netmiko_huawei_vrp",  # Discovery script called by tasks.py
        },
        "netmiko_linux": {
            "name": "Netmiko Linux",
            "platform": "linux",  # Netmiko type, used by Nornir
            "protocol": "ssh",
            "framework": "netmiko",
            "discovery_script": "netmiko_linux",  # Discovery script called by tasks.py
        },
        "json_vmware_vsphere": {
            "name": "VMware vSphere",
            "platform": "vmware_vsphere",  #
            "protocol": "https",
            "framework": "json",
            "discovery_script": "json_vmware_vsphere",  # Discovery script called by tasks.py
        },
        "xml_panw_ngfw": {
            "name": "Palo Alto Networks NGFW",
            "platform": "panw_ngfw",  #
            "protocol": "https",
            "framework": "xml",
            "discovery_script": "xml_panw_ngfw",  # Discovery script called by tasks.py
        },
    }

    CHOICES = [(key, value.get("name")) for key, value in MODES.items()]


class FilterModeChoices(ChoiceSet):
    """Filter types used in NetDoc scripts."""

    CHOICES = [
        ("include", "Include only"),
        ("exclude", "Exclude"),
    ]


class RouteTypeChoices(ChoiceSet):
    """Route type."""

    CHOICES = [
        ("u", "Unknown"),
        ("b", "BGP"),
        ("c", "Connected"),
        ("s", "Static"),
        ("u", "User-space"),
        ("r", "RIP"),
        ("e", "EIGRP"),
        ("ex", "EIGRP external"),
        ("o", "OSPF intra area"),
        ("oia", "OSPF inter area"),
        ("on1", "OSPF NSSA external type 1"),
        ("on2", "OSPF NSSA external type 2"),
        ("oe1", "OSPF external type 1"),
        ("oe2", "OSPF external type 2"),
        ("i", "IS-IS"),
        ("is", "IS-IS summary"),
        ("i1", "IS-IS level-1"),
        ("i2", "IS-IS level-2"),
    ]
