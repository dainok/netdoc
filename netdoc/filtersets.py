"""Advanced filters."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from django.db.models import Q

from netbox.filtersets import NetBoxModelFilterSet

from netdoc.models import (
    Discoverable,
    Credential,
    DiscoveryLog,
    ArpTableEntry,
    MacAddressTableEntry,
    RouteTableEntry,
)


class ArpTableEntryFilterSet(NetBoxModelFilterSet):
    """FilterSet used in ArpTableListView."""

    class Meta:
        """FilterSet metadata."""

        model = ArpTableEntry
        fields = []

    def search(self, queryset, name, value):
        """Generic (quick) search."""
        return queryset.filter(
            Q(ip_address__icontains=value)
            | Q(mac_address__icontains=value)
            | Q(interface__name__icontains=value)
            | Q(interface__device__name__icontains=value)
            | Q(virtual_interface__name__icontains=value)
            | Q(virtual_interface__virtual_machine__name__icontains=value)
            | Q(vendor__icontains=value)
        )


class CredentialFilterSet(NetBoxModelFilterSet):
    """FilterSet used in Credential."""

    class Meta:
        """FilterSet metadata."""

        model = Credential
        fields = []

    def search(self, queryset, name, value):
        """Generic (quick) search."""
        return queryset.filter(Q(name__icontains=value) | Q(username__icontains=value))


class DiscoverableFilterSet(NetBoxModelFilterSet):
    """FilterSet used in Discoverable."""

    class Meta:
        """FilterSet metadata."""

        model = Discoverable
        fields = ["site", "credential", "mode", "discoverable"]

    def search(self, queryset, name, value):
        """Generic (quick) search."""
        return queryset.filter(
            Q(address__icontains=value)
            | Q(device__name__icontains=value)
            | Q(vm__name__icontains=value)
            | Q(site__name__icontains=value)
            | Q(credential__name__icontains=value)
            | Q(mode__icontains=value)
        )


class DiscoveryLogFilterSet(NetBoxModelFilterSet):
    """FilterSet used in DiscoveryLog."""

    class Meta:
        """FilterSet metadata."""

        model = DiscoveryLog
        fields = [
            "discoverable__device",
            "discoverable__vm",
            "configuration",
            "success",
            "supported",
            "parsed",
            "ingested",
        ]

    def search(self, queryset, name, value):
        """Generic (quick) search."""
        return queryset.filter(
            Q(discoverable__address__icontains=value)
            | Q(discoverable__mode__icontains=value)
            | Q(discoverable__device__name__icontains=value)
            | Q(discoverable__vm__name__icontains=value)
            | Q(command__icontains=value)
        )


class MacAddressTableEntryFilterSet(NetBoxModelFilterSet):
    """FilterSet used in MacAddressTableListView."""

    class Meta:
        """FilterSet metadata."""

        model = MacAddressTableEntry
        fields = []

    def search(self, queryset, name, value):
        """Generic (quick) search."""
        return queryset.filter(
            Q(mac_address__icontains=value)
            | Q(interface__name__icontains=value)
            | Q(interface__device__name__icontains=value)
            | Q(vendor__icontains=value)
        )


class RouteTableEntryFilterSet(NetBoxModelFilterSet):
    """FilterSet used in RouteTableEntryListView."""

    class Meta:
        """FilterSet metadata."""

        model = RouteTableEntry
        fields = []

    def search(self, queryset, name, value):
        """Generic (quick) search."""
        return queryset.filter(
            Q(device__name__icontains=value)
            | Q(vm__name__icontains=value)
            | Q(destination__icontains=value)
            | Q(protocol__icontains=value)
            | Q(nexthop_ip__icontains=value)
            | Q(nexthop_if__name__icontains=value)
            | Q(nexthop_virtual_if__name__icontains=value)
            | Q(vrf__name__icontains=value)
        )
