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
from OuiLookup import OuiLookup

from django.db import models
from django.urls import reverse

from ipam.fields import IPAddressField
from dcim.fields import MACAddressField
from utilities.choices import ChoiceSet
from netbox.models import NetBoxModel

from netdoc.utils import parse_netmiko_output, CONFIG_COMMANDS, FAILURE_OUTPUT


class DeviceImageChoices(ChoiceSet):
    """Image used in diagrams associated to device roles."""

    CHOICES = [
        ("access-switch", "Access Switch"),
        ("backup", "Backup Device"),
        ("circuit", "Circuit"),
        ("core-switch", "Core Switch"),
        ("distribution-switch", "Distribution Switch"),
        ("firewall", "Firewall"),
        ("internal-switch", "Internal Switch"),
        ("isp-cpe-material", "ISP CPE Material"),
        ("non-racked-devices", "Non Racked Device"),
        ("power-feed", "Power Feed"),
        ("power-panel", "Power Panel"),
        ("power-units", "Power Units"),
        ("provider-networks", "Provider Networks"),
        ("unknown", "Unknown"),
        ("router", "Router"),
        ("server", "Server"),
        ("storage", "Storage"),
        ("wan-network", "WAN Network"),
        ("wireless-ap", "Wireless AP"),
    ]


class DiagramModeChoices(ChoiceSet):
    """Diagram mode."""

    CHOICES = [
        ("l2", "L2"),
        ("l3", "L3"),
        # ("stp", "STP"),
    ]


class DiscoveryModeChoices(ChoiceSet):
    """Discovey mode."""

    CHOICES = [
        ("netmiko_cisco_ios", "Netmiko Cisco IOS XE"),
        ("netmiko_cisco_nxos", "Netmiko Cisco NX-OS"),
        ("netmiko_cisco_xr", "Netmiko Cisco XR"),
        ("netmiko_hp_comware", "Netmiko HPE Comware"),
        ("netmiko_linux", "Netmiko Linux"),
    ]


class RouteTypeChoices(ChoiceSet):
    """Route type."""

    CHOICES = [
        ("u", "Unknown"),
        ("b", "BGP"),
        ("c", "Connected"),
        ("s", "Static"),
        ("r", "RIP"),
        ("e", "EIGRP"),
        ("ex", "EIGRP external"),
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
    )
    ip_address = IPAddressField(help_text="IPv4 address", editable=False)
    mac_address = MACAddressField(help_text="MAC Address", editable=False)
    vendor = models.CharField(
        max_length=255, blank=True, null=True, help_text="Vendor", editable=False
    )  #: Vendor (from OUI)

    class Meta:
        """Database metadata."""

        ordering = ["ip_address"]
        unique_together = ["interface", "ip_address", "mac_address"]
        verbose_name = "ARP table entry"
        verbose_name_plural = "ARP table entries"

    def __str__(self):
        """Return a human readable name when the object is printed."""
        return f"{self.ip_address} has {self.mac_address} at {self.interface}"

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
    enable_password = models.CharField(
        max_length=100,
        blank=True,
    )
    password = models.CharField(
        max_length=100,
        blank=True,
    )
    username = models.CharField(
        max_length=100,
        blank=True,
    )

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

    class Meta:
        """Database metadata."""

        ordering = ["mode", "address"]
        unique_together = ["address", "mode"]
        verbose_name = "Device"
        verbose_name_plural = "Devices"

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

    def __str__(self):
        """Return a human readable name when the object is printed."""
        return f"{self.command} at {self.created}"

    def get_absolute_url(self):
        """Return the absolute url."""
        return reverse("plugins:netdoc:discoverylog", args=[self.pk])

    def parse(self):
        """Parse raw_output."""
        self.configuration = False
        self.success = False
        self.parsed = False
        self.parsed_output = ""
        mode = self.discoverable.mode  # pylint: disable=no-member

        # Check if the command is supported
        if not self.supported:
            return

        # Check if the output is a configuration file
        if self.template != "HOSTNAME":
            for regex in CONFIG_COMMANDS:
                if re.search(regex, self.command):
                    self.configuration = True
                    # Configuraion file -> skip parsing
                    return

        # Check if the output is completed successfully
        for regex in FAILURE_OUTPUT:
            if re.search(regex, self.raw_output):
                # Command failed -> skip parsing
                return
        self.success = True

        # Parse framework (e.g. netmiko) and platform (e.g. cisco_ios)
        framework = mode.split("_").pop(0)
        platform = "_".join(mode.split("_")[1:])

        if framework == "netmiko":
            parsed_output, parsed = parse_netmiko_output(
                self.raw_output, self.command, platform, template=self.template
            )
        else:
            raise ValueError("Framework not detected")

        self.parsed_output = parsed_output
        self.parsed = parsed

    def save(self, *args, **kwargs):
        """Parse raw_output when saving."""
        if "supported" in dict(self.details):
            self.supported = dict(self.details).get("supported")
        if not self.pk:
            # Prase (once) before creating the object
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
        ]
        verbose_name = "Route"
        verbose_name_plural = "Routes"

    def __str__(self):
        """Return a human readable name when the object is printed."""
        if self.nexthop_ip:
            return f"{self.destination} [{self.distance}/{self.metric}] via {self.nexthop_ip}"
        # Assuming nexthop_if
        return (
            f"{self.destination} [{self.distance}/{self.metric}] at {self.nexthop_if}"
        )

    def get_absolute_url(self):
        """Return the absolute url."""
        return reverse("plugins:netdoc:routingtable", args=[self.pk])
