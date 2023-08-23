"""Tables, called by Views."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import django_tables2 as tables

from netbox.tables import NetBoxTable, ChoiceFieldColumn
from netbox.tables.columns import ActionsColumn

from netdoc import models


#
# ArpTableEntry tables
#


class ArpTableEntryTable(NetBoxTable):
    """ARP list table used in ArpTableEntryView."""

    meta_device = tables.Column(linkify=True, verbose_name="Device", orderable=False)
    meta_interface = tables.Column(
        linkify=True, verbose_name="Interface", orderable=False
    )
    mac_address = tables.LinkColumn(
        "plugins:netdoc:arptableentry",
        args=[tables.utils.A("pk")],
        verbose_name="MAC address",
    )
    meta_role = tables.Column(verbose_name="Role", orderable=False)
    ip_address = tables.LinkColumn(
        "plugins:netdoc:arptableentry",
        args=[tables.utils.A("pk")],
        verbose_name="IP address",
    )
    actions = []  # Read only table

    class Meta(NetBoxTable.Meta):
        """Table metadata."""

        model = models.ArpTableEntry
        fields = [
            "pk",
            "id",
            "meta_device",
            "meta_role",
            "meta_interface",
            "ip_address",
            "mac_address",
            "vendor",
            "last_updated",
            "created",
        ]
        default_columns = [
            "meta_device",
            "meta_role",
            "meta_interface",
            "ip_address",
            "mac_address",
            "vendor",
            "last_updated",
        ]


#
# Credential tables
#


class CredentialTable(NetBoxTable):
    """Credential list table used in CredentialListView."""

    name = tables.Column(linkify=True)
    discoverables_count = tables.Column(verbose_name="Discoverables")

    class Meta(NetBoxTable.Meta):
        """Table metadata."""

        model = models.Credential
        fields = ["pk", "id", "name", "username", "verify_cert", "discoverables_count"]
        default_columns = ["name", "username", "verify_cert", "discoverables_count"]


#
# Diagram tables
#


class DiagramTable(NetBoxTable):
    """Diagram list table used in DiagramListView."""

    name = tables.Column(linkify=True)

    class Meta(NetBoxTable.Meta):
        """Table metadata."""

        model = models.Diagram
        fields = ["pk", "id", "name", "mode", "created", "last_updated"]
        default_columns = ["name", "mode", "created", "last_updated"]


#
# Discoverable tables
#


class DiscoverableTable(NetBoxTable):
    """Credential list table used in DiscoverableListView."""

    address = tables.Column(linkify=True)
    meta_device = tables.Column(linkify=True, verbose_name="Device", orderable=False)
    mode = ChoiceFieldColumn()
    # discoverylogs_count = tables.Column(verbose_name="Logs")
    discovery_button = """
    <a class="btn btn-sm btn-secondary" href="{% url 'plugins:netdoc:discoverable_discover' pk=record.pk %}" title="Discover">
        <i class="mdi mdi-refresh"></i>
    </a>
    """
    actions = ActionsColumn(extra_buttons=discovery_button)

    class Meta(NetBoxTable.Meta):
        """Table metadata."""

        model = models.Discoverable
        fields = [
            "pk",
            "id",
            "address",
            "meta_device",
            "site",
            "credential",
            "mode",
            "discoverable",
            "last_discovered_at",
            # "discoverylogs_count",
            "last_updated",
            "created",
        ]
        default_columns = [
            "address",
            "meta_device",
            "site",
            "credential",
            "mode",
            "discoverable",
            "last_discovered_at",
            # "discoverylogs_count",
        ]


class DiscoverableTableWOLogCount(NetBoxTable):
    """Discoverable list table used in CredentialView.

    DiscoveryLog count is omitted.
    """

    address = tables.Column(linkify=True)
    meta_device = tables.Column(linkify=True, verbose_name="Device", orderable=False)
    mode = ChoiceFieldColumn()
    discovery_button = """
    <a class="btn btn-sm btn-secondary" href="{% url 'plugins:netdoc:discoverable_discover' pk=record.pk %}" title="Discover">
        <i class="mdi mdi-refresh"></i>
    </a>
    """
    actions = ActionsColumn(extra_buttons=discovery_button)

    class Meta(NetBoxTable.Meta):
        """Table metadata."""

        model = models.Discoverable
        fields = [
            "pk",
            "id",
            "address",
            "meta_device",
            "site",
            "credential",
            "mode",
            "discoverable",
            "last_discovered_at",
            "last_updated",
            "created",
        ]
        default_columns = [
            "address",
            "meta_device",
            "site",
            "credential",
            "mode",
            "discoverable",
            "last_discovered_at",
        ]


#
# Discovery log tables
#


class DiscoveryLogTable(NetBoxTable):
    """Credential list table used in DiscoveryLogListView."""

    device = tables.Column(linkify=True, accessor="discoverable.device")
    meta_device = tables.Column(linkify=True, verbose_name="Device", orderable=False)
    vm = tables.Column(linkify=True, accessor="discoverable.vm")
    discoverable = tables.Column(linkify=True)
    actions = ActionsColumn(actions=("delete",))  # Read only + delete table

    class Meta(NetBoxTable.Meta):
        """Table metadata."""

        model = models.DiscoveryLog
        fields = [
            "pk",
            "id",
            "created",
            "discoverable",
            "meta_device",
            "command",
            "template",
            "order",
            "configuration",
            "supported",
            "success",
            "parsed",
            "ingested",
            "last_updated",
        ]
        default_columns = [
            "id",
            "created",
            "discoverable",
            "meta_device",
            "command",
            "configuration",
            "supported",
            "success",
            "parsed",
            "ingested",
        ]


#
# MacAddressTableEntry tables
#


class MacAddressTableEntryTable(NetBoxTable):
    """MAC address list table used in MacAddressTableListView."""

    device = tables.LinkColumn(
        "dcim:device",
        accessor="interface.device",
        args=[tables.utils.A("interface__device__pk")],
    )
    interface = tables.LinkColumn(
        "dcim:interface", args=[tables.utils.A("interface__pk")]
    )
    mac_address = tables.LinkColumn(
        "plugins:netdoc:macaddresstableentry", args=[tables.utils.A("pk")]
    )
    device_role = tables.Column(accessor="interface.device.device_role")
    vvid = tables.Column(verbose_name="VLAN")
    actions = []  # Read only table

    class Meta(NetBoxTable.Meta):
        """Table metadata."""

        model = models.MacAddressTableEntry
        fields = [
            "pk",
            "id",
            "device",
            "device_role",
            "interface",
            "vvid",
            "mac_address",
            "vendor",
            "last_updated",
            "created",
        ]
        default_columns = [
            "device",
            "device_role",
            "interface",
            "vvid",
            "mac_address",
            "vendor",
            "last_updated",
        ]


#
# RouteTableEntry tables
#


class RouteTableEntryTable(NetBoxTable):
    """Route list table used in RouteTableEntryListView."""

    destination = tables.Column(linkify=True)

    meta_device = tables.Column(linkify=True, verbose_name="Device", orderable=False)
    meta_nexthop_if = tables.Column(
        linkify=True, verbose_name="Nexthop IF", orderable=False
    )
    nexthop_ip = tables.Column(verbose_name="Nexthop IP")
    vrf = tables.LinkColumn(
        "ipam:vrf", args=[tables.utils.A("vrf__pk")], verbose_name="VRF"
    )
    device_role = tables.Column(accessor="device.device_role")
    actions = []  # Read only table

    class Meta(NetBoxTable.Meta):
        """Table metadata."""

        model = models.RouteTableEntry
        fields = [
            "pk",
            "id",
            "meta_device",
            "device_role",
            "destination",
            "protocol",
            "distance",
            "metric",
            "nexthop_ip",
            "meta_nexthop_if",
            "vrf",
            "last_updated",
            "created",
        ]
        default_columns = [
            "meta_device",
            "destination",
            "protocol",
            "distance",
            "metric",
            "nexthop_ip",
            "meta_nexthop_if",
            "vrf",
            "last_updated",
        ]
