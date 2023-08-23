"""Models (ORM).

Define ORM models for NetDoc objects:
* A Discoverable is a device willed to be discovered using a specific mode.
* Credential is associated to one or more Discoverables.
* A DiscoveryLog is the output for a specific discovery command executed in a Discoverable.
"""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import re
import json
import base64
from xml.parsers.expat import ExpatError
import xmltodict
from cryptography.fernet import Fernet, InvalidToken
from OuiLookup import OuiLookup

from django.db import models
from django.urls import reverse
from django.conf import settings

from ipam.fields import IPAddressField
from dcim.fields import MACAddressField
from utilities.choices import ChoiceSet
from netbox.models import NetBoxModel

from netdoc.utils import (
    parse_netmiko_output,
    CONFIG_COMMANDS,
    FAILURE_OUTPUT,
    is_command_supported,
)

SECRET_KEY = settings.SECRET_KEY.encode("utf-8")
FERNET_KEY = base64.urlsafe_b64encode(SECRET_KEY.ljust(32)[:32])
CREDENTIAL_ENCRYPTED_FIELDS = [
    "password",
    "enable_password",
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

    CHOICES = [
        ("netmiko_cisco_ios", "Netmiko Cisco IOS XE"),
        ("netmiko_cisco_ios_telnet", "Netmiko Cisco IOS XE (Telnet)"),
        ("netmiko_cisco_nxos", "Netmiko Cisco NX-OS"),
        ("netmiko_cisco_xr", "Netmiko Cisco XR"),
        ("netmiko_hp_comware", "Netmiko HPE Comware"),
        ("netmiko_hp_procurve", "Netmiko HPE Procurve"),
        ("netmiko_linux", "Netmiko Linux"),
        ("json_vmware_vsphere", "VMware vSphere"),
        ("xml_panw_ngfw", "Palo Alto Networks NGFW"),
    ]


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


#
# ARPEntry model
#


class ArpTableEntry(NetBoxModel):
    """
    Model for ArpTableEntry.

    Each ARP seen on each network interface is
    counted. One IP Address can be associated to one MAC Address. One MAC
    Address can be associated to multiple IP Addresses.
    """

    interface = models.ForeignKey(
        to="dcim.Interface",
        on_delete=models.CASCADE,
        related_name="+",
        editable=False,
        blank=True,
        null=True,
    )
    ip_address = IPAddressField(help_text="IPv4 address", editable=False)
    mac_address = MACAddressField(help_text="MAC Address", editable=False)
    vendor = models.CharField(
        max_length=255, blank=True, null=True, help_text="Vendor", editable=False
    )  #: Vendor (from OUI)
    virtual_interface = models.ForeignKey(
        to="virtualization.VMInterface",
        on_delete=models.CASCADE,
        related_name="+",
        editable=False,
        blank=True,
        null=True,
    )

    class Meta:
        """Database metadata."""

        ordering = ["ip_address"]
        unique_together = [
            "interface",
            "ip_address",
            "mac_address",
            "virtual_interface",
        ]
        verbose_name = "ARP table entry"
        verbose_name_plural = "ARP table entries"

    @property
    def meta_interface(self):
        """
        Define meta_interface property.

        meta_interface return Device or VM, if set.
        """
        if self.interface:
            return self.interface
        if self.virtual_interface:
            return self.virtual_interface
        return None

    @property
    def meta_role(self):
        """
        Role meta_role property.

        meta_role return device/vm role, if set.
        """
        if (
            self.interface
            and self.interface.device.device_role  # pylint: disable=no-member
        ):
            return self.interface.device.device_role.name  # pylint: disable=no-member
        if (
            self.virtual_interface
            and self.virtual_interface.virtual_machine.role  # pylint: disable=no-member
        ):
            return (
                self.virtual_interface.virtual_machine.role.name  # pylint: disable=no-member
            )
        return None

    @property
    def meta_device(self):
        """
        Define meta_device property.

        meta_device return Device or VM, if set.
        """
        if self.interface:
            return self.interface.device  # pylint: disable=no-member
        if self.virtual_interface:
            return self.virtual_interface.virtual_machine  # pylint: disable=no-member
        return None

    def __str__(self):
        """Return a human readable name when the object is printed."""
        if self.interface:
            return f"{self.ip_address} has {self.mac_address} at {self.interface}"
        return f"{self.ip_address} has {self.mac_address} at {self.virtual_interface}"

    def get_absolute_url(self):
        """Return the absolute url."""
        return reverse("plugins:netdoc:arptableentry", args=[self.pk])

    def save(self, *args, **kwargs):
        """Set vendor field when saving."""
        self.vendor = list(
            OuiLookup().query(str(self.mac_address)).pop().values()
        ).pop()
        super().save(*args, **kwargs)


#
# Credential model
#


class Credential(NetBoxModel):
    """Model for Credential."""

    name = models.CharField(max_length=100)
    enable_password = models.TextField(blank=True)
    password = models.TextField(blank=True)
    username = models.CharField(
        max_length=100,
        blank=True,
    )
    verify_cert = models.BooleanField(default=True, help_text="Validate certificate")

    class Meta:
        """Database metadata."""

        ordering = ["name"]
        unique_together = ["name"]
        verbose_name = "Credential"
        verbose_name_plural = "Credentials"

    def __str__(self):
        """Return a human readable name when the object is printed."""
        return str(self.name)

    def get_absolute_url(self):
        """Return the absolute url."""
        return reverse("plugins:netdoc:credential", args=[self.pk])

    def get_secrets(self):
        """Get clear text password."""
        fernet_o = Fernet(FERNET_KEY)
        secrets = {}
        for field in CREDENTIAL_ENCRYPTED_FIELDS:
            original_secret = getattr(self, field)
            if original_secret:
                # Check if already decrypted
                try:
                    secret = fernet_o.decrypt(
                        original_secret.encode()  # pylint: disable=no-member
                    ).decode()
                except InvalidToken:
                    secret = original_secret
            else:
                secret = None
            secrets[field] = secret
        return secrets


#
# Diagram model
#


class Diagram(NetBoxModel):
    """Model for Diagram."""

    details = models.JSONField(
        default=dict,
    )  #: Vis.Js Details in JSON format
    device_roles = models.ManyToManyField(
        to="dcim.DeviceRole",
        related_name="+",
        blank=True,
    )
    mode = models.CharField(
        max_length=30,
        choices=DiagramModeChoices,
    )
    name = models.CharField(max_length=100)
    sites = models.ManyToManyField(
        to="dcim.Site",
        related_name="+",
        blank=True,
    )
    vrfs = models.ManyToManyField(
        to="ipam.VRF",
        related_name="+",
        blank=True,
    )
    include_global_vrf = models.BooleanField(
        default=False
    )  #: Always include Global VRF (None)

    class Meta:
        """Database metadata."""

        ordering = ["name"]
        unique_together = [
            "name",
        ]
        verbose_name = "Diagram"
        verbose_name_plural = "Diagrams"

    def __str__(self):
        """Return a human readable name when the object is printed."""
        return str(self.name)

    def get_absolute_url(self):
        """Return the absolute url."""
        return reverse("plugins:netdoc:diagram", args=[self.pk])


#
# Discoverable model
#


class Discoverable(NetBoxModel):
    """Model for Discoverable."""

    address = models.GenericIPAddressField()
    device = models.OneToOneField(
        to="dcim.Device",
        editable=False,
        on_delete=models.SET_NULL,
        related_name="+",
        blank=True,
        null=True,
    )
    credential = models.ForeignKey(
        to=Credential,
        on_delete=models.PROTECT,
        related_name="discoverables",
    )
    mode = models.CharField(
        max_length=30,
        choices=DiscoveryModeChoices,
    )
    discoverable = models.BooleanField(
        default=False
    )  #: New created devices have discoverable=False by default (e.g. if created from CDP/LLDP)
    last_discovered_at = models.DateTimeField(blank=True, null=True, editable=False)
    site = models.ForeignKey(
        to="dcim.Site",
        on_delete=models.CASCADE,
        related_name="+",
    )
    vm = models.OneToOneField(
        to="virtualization.VirtualMachine",
        editable=False,
        on_delete=models.SET_NULL,
        related_name="+",
        blank=True,
        null=True,
    )

    class Meta:
        """Database metadata."""

        ordering = ["mode", "address"]
        unique_together = ["address", "mode"]
        verbose_name = "Device"
        verbose_name_plural = "Devices"

    @property
    def meta_device(self):
        """
        Define meta_device property.

        meta_device return Device or VM, if set.
        """
        if self.device:
            return self.device
        if self.vm:
            return self.vm
        return None

    def __str__(self):
        """Return a human readable name when the object is printed."""
        return f"{self.address} via {self.mode}"

    def get_absolute_url(self):
        """Return the absolute url."""
        return reverse("plugins:netdoc:discoverable", args=[self.pk])


#
# Discovery log model
#


class DiscoveryLog(NetBoxModel):
    """Model for DiscoveryLog."""

    command = models.CharField(
        max_length=255, editable=False
    )  #: Exact CMD used to discover
    configuration = models.BooleanField(
        default=False,
        editable=False,
    )
    discoverable = models.ForeignKey(
        to=Discoverable,
        on_delete=models.CASCADE,
        related_name="discoverylogs",
        editable=False,
    )
    details = models.JSONField(
        default=dict,
        editable=False,
    )  #: Details in JSON format stored within Nornir task name
    order = models.IntegerField(default=128)  #: Order to ingest (lower is sooner)
    parsed_output = models.JSONField(default=list, editable=False)
    raw_output = models.JSONField(
        default=dict,
    )
    template = models.CharField(
        max_length=255, editable=False
    )  #: Template used to ingest parsed_output
    success = models.BooleanField(
        default=False, editable=False
    )  # True if excuting request return OK and raw_output is valid (avoid command not found)
    supported = models.BooleanField(
        default=True, editable=False
    )  #: False if output is unsupported (won't be parsed/ingested)
    parsed = models.BooleanField(
        default=False, editable=False
    )  #: True if parsing raw_output return a valid JSON
    ingested = models.BooleanField(
        default=False, editable=False
    )  #: True if all data are ingested without errors

    class Meta:
        """Database metadata."""

        ordering = ["created"]
        verbose_name = "Log"
        verbose_name_plural = "Logs"

    @property
    def meta_device(self):
        """
        Define meta_device property.

        meta_device return Device or VM, if set.
        """
        if self.discoverable.device:  # pylint: disable=no-member
            return self.discoverable.device  # pylint: disable=no-member
        if self.discoverable.vm:  # pylint: disable=no-member
            return self.discoverable.vm  # pylint: disable=no-member
        return None

    def __str__(self):
        """Return a human readable name when the object is printed."""
        return f"{self.command} at {self.created}"

    def get_absolute_url(self):
        """Return the absolute url."""
        return reverse("plugins:netdoc:discoverylog", args=[self.pk])

    def parse(self):
        """Parse raw_output."""
        self.success = False
        self.parsed = False
        self.parsed_output = ""

        # Check if the command is supported
        if not self.supported:
            return

        # Check if the output is completed successfully
        for regex in FAILURE_OUTPUT:
            if re.search(regex, self.raw_output):
                # Command failed -> skip parsing
                return
        self.success = True

        # Parse framework (e.g. netmiko) and platform (e.g. cisco_ios)
        framework = self.details.get("framework")
        platform = self.details.get("platform")

        if self.template == "HOSTNAME":
            # Logs tracking hostnames are parsed during ingestion phase
            parsed = True
            parsed_output = ""
        else:
            if framework == "netmiko":
                parsed_output, parsed = parse_netmiko_output(
                    self.raw_output, self.command, platform, template=self.template
                )
            elif framework == "json":
                try:
                    parsed = True
                    parsed_output = json.loads(self.raw_output)
                except TypeError as exc:
                    parsed = False
                    parsed_output = str(exc)
                except json.decoder.JSONDecodeError as exc:
                    parsed = False
                    parsed_output = str(exc)
            elif framework == "xml":
                try:
                    parsed = True
                    parsed_output = xmltodict.parse(self.raw_output)
                except TypeError as exc:
                    parsed = False
                    parsed_output = str(exc)
                except ExpatError as exc:
                    parsed = False
                    parsed_output = str(exc)
            else:
                raise ValueError(f"Framework {framework} not implemented")

        self.parsed_output = parsed_output
        self.parsed = parsed

    def save(self, *args, **kwargs):
        """Set supported flag and parse raw_output when creating."""
        if not self.pk:
            # Check if command is supported
            mode = self.discoverable.mode  # pylint: disable=no-member
            framework = mode.split("_")[0]
            platform = "_".join(mode.split("_")[1:3])
            try:
                protocol = mode.split("_")[3]  # pylint: disable=no-member
            except IndexError:
                protocol = "default"
            template = self.template
            supported = is_command_supported(framework, platform, template)

            # Check if the command is a configuration file
            configuration = False
            for regex in CONFIG_COMMANDS:
                if re.search(regex, self.command):
                    configuration = True

            # Update log details
            details = self.details
            details["framework"] = framework
            details["platform"] = platform
            details["protocol"] = protocol
            self.supported = supported
            self.details = details
            self.configuration = configuration

            # Parse
            self.parse()

        super().save(*args, **kwargs)


#
# MacAddressTableEntry model
#


class MacAddressTableEntry(NetBoxModel):
    """Model for MacAddressTableEntry.

    Each MAC Address seen on each network
    interface is counted. One IP Address can be associated to one AC
    Address. One MAC Address can be associated to multiple IP Addresses.
    """

    interface = models.ForeignKey(
        to="dcim.Interface",
        on_delete=models.CASCADE,
        related_name="+",
        editable=False,
    )
    mac_address = MACAddressField(help_text="MAC Address", editable=False)
    vendor = models.CharField(
        max_length=255, blank=True, null=True, help_text="Vendor", editable=False
    )  #: Vendor (from OUI)
    vvid = models.IntegerField(help_text="VLAN ID")  #: VLAN ID (TAG)

    class Meta:
        """Database metadata."""

        ordering = ["mac_address", "vvid"]
        unique_together = ["interface", "mac_address", "vvid"]
        verbose_name = "MAC Address table entry"
        verbose_name_plural = "MAC Address table entries"

    def __str__(self):
        """Return a human readable name when the object is printed."""
        return f"{self.mac_address} is at {self.interface}"

    def get_absolute_url(self):
        """Return the absolute url."""
        return reverse("plugins:netdoc:macaddresstableentry", args=[self.pk])

    def save(self, *args, **kwargs):
        """Set vendor field when saving."""
        self.vendor = list(
            OuiLookup().query(str(self.mac_address)).pop().values()
        ).pop()
        super().save(*args, **kwargs)


#
# RouteTableEntry model
#


class RouteTableEntry(NetBoxModel):
    """Model for RouteTableEntry.

    Each route has a destination, type (connected, static...),
    nexthop_ip and/or nexthop_if, distance (administrative), metric.
    """

    destination = IPAddressField(help_text="Destination network", editable=False)
    device = models.ForeignKey(
        to="dcim.Device",
        on_delete=models.CASCADE,
        related_name="+",
        blank=True,
        null=True,
    )
    distance = models.IntegerField(blank=True, null=True, editable=False)
    metric = models.BigIntegerField(blank=True, null=True, editable=False)
    nexthop_ip = IPAddressField(
        help_text="IPv4 address",
        editable=False,
        blank=True,
        null=True,
    )
    nexthop_if = models.ForeignKey(
        to="dcim.Interface",
        on_delete=models.CASCADE,
        related_name="+",
        editable=False,
        blank=True,
        null=True,
    )
    nexthop_virtual_if = models.ForeignKey(
        to="virtualization.VMInterface",
        on_delete=models.CASCADE,
        related_name="+",
        editable=False,
        blank=True,
        null=True,
    )
    protocol = models.CharField(
        max_length=30,
        choices=RouteTypeChoices,
        editable=False,
    )
    vrf = models.ForeignKey(
        to="ipam.VRF",
        on_delete=models.CASCADE,
        related_name="+",
        editable=False,
        blank=True,
        null=True,
    )
    vm = models.ForeignKey(
        to="virtualization.VirtualMachine",
        editable=False,
        on_delete=models.SET_NULL,
        related_name="+",
        blank=True,
        null=True,
    )

    class Meta:
        """Database metadata."""

        ordering = ["device", "protocol", "metric"]
        unique_together = [
            "device",
            "destination",
            "distance",
            "metric",
            "protocol",
            "vrf",
            "nexthop_if",
            "nexthop_virtual_if",
            "nexthop_ip",
            "vm",
        ]
        verbose_name = "Route"
        verbose_name_plural = "Routes"

    @property
    def meta_nexthop_if(self):
        """
        Define meta_nexthop_if property.

        meta_nexthop_if return Device or VM, if set.
        """
        if self.nexthop_virtual_if:
            return self.nexthop_virtual_if
        if self.nexthop_if:
            return self.nexthop_if
        return None

    @property
    def meta_device(self):
        """
        Define meta_device property.

        meta_device return Device or VM, if set.
        """
        if self.device:
            return self.device
        if self.vm:
            return self.vm
        return None

    def __str__(self):
        """Return a human readable name when the object is printed."""
        if self.nexthop_ip:
            return (
                f"{self.destination} {self.protocol}"
                + f" [{self.distance}/{self.metric}] via {self.nexthop_ip}"
            )
        # Assuming nexthop_if
        return (
            f"{self.destination} {self.protocol}"
            + f" [{self.distance}/{self.metric}] at {self.nexthop_if}"
        )

    def get_absolute_url(self):
        """Return the absolute url."""
        return reverse("plugins:netdoc:routetableentry", args=[self.pk])
