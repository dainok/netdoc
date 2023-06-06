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

    device = tables.LinkColumn(
        "dcim:device",
        accessor="interface.device",
        args=[tables.utils.A("interface__device__pk")],
    )
    interface = tables.LinkColumn(
        "dcim:interface", args=[tables.utils.A("interface__pk")]
    )
    mac_address = tables.LinkColumn(
        "plugins:netdoc:arptableentry", args=[tables.utils.A("pk")]
    )
    device_role = tables.Column(accessor="interface.device.device_role")
    actions = []  # Read only table

    class Meta(NetBoxTable.Meta):
        """Table metadata."""

        model = models.ArpTableEntry
        fields = [
            "pk",
            "id",
            "device",
            "device_role",
            "interface",
            "ip_address",
            "mac_address",
            "vendor",
            "last_updated",
            "created",
        ]
        default_columns = [
            "device",
            "device_role",
            "interface",
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
    discoverables_count = tables.Column()

    class Meta(NetBoxTable.Meta):
        """Table metadata."""

        model = models.Credential
        fields = ["pk", "id", "name", "username", "discoverables_count"]
        default_columns = ["name", "username", "discoverables_count"]


#
# Diagram tables
#


class DiagramTable(NetBoxTable):
    """Diagram list table used in DiagramListView."""

    name = tables.Column(linkify=True)
    discoverables_count = tables.Column()

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
    device = tables.Column(linkify=True)
    mode = ChoiceFieldColumn()
    discoverylogs_count = tables.Column()
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
            "device",
            "site",
            "credential",
            "mode",
            "discoverable",
            "last_discovered_at",
            "discoverylogs_count",
            "last_updated",
            "created",
        ]
        default_columns = [
            "address",
            "device",
            "site",
            "credential",
            "mode",
            "discoverable",
            "last_discovered_at",
            "discoverylogs_count",
        ]


class DiscoverableTableWOLogCount(NetBoxTable):
    """Credential list table used in DiscoverableListView.

    DiscoveryLog count is omitted. Used in CredentialView.
    """

    address = tables.Column(linkify=True)
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
            "device",
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
            "device",
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
            "device",
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
            "device",
            "command",
            "order",
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

    device = tables.LinkColumn(
        "dcim:device",
        args=[tables.utils.A("device__pk")],
    )
    nexthop_if = tables.LinkColumn(
        "dcim:interface", args=[tables.utils.A("nexthop_if__pk")]
    )
    vrf = tables.LinkColumn("ipam:vrf", args=[tables.utils.A("vrf__pk")])
    device_role = tables.Column(accessor="device.device_role")
    actions = []  # Read only table

    class Meta(NetBoxTable.Meta):
        """Table metadata."""

        model = models.RouteTableEntry
        fields = [
            "pk",
            "id",
            "device",
            "device_role",
            "destination",
            "protocol",
            "distance",
            "metric",
            "nexthop_ip",
            "nexthop_if",
            "vrf",
            "last_updated",
            "created",
        ]
        default_columns = [
            "device",
            "destination",
            "protocol",
            "distance",
            "metric",
            "nexthop_ip",
            "nexthop_if",
            "vrf",
            "last_updated",
        ]
