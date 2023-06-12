"""
Global search.

Remembet to reindex after changes: python manage.py reindex netdoc
"""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netbox.search import SearchIndex, register_search
from .models import ArpTableEntry, MacAddressTableEntry, RouteTableEntry


@register_search
class ArpTableEntryIndex(SearchIndex):
    """Includes ArpTableEntry in global search."""

    model = ArpTableEntry
    fields = [
        ["ip_address", 100],
        ["mac_address", 100],
        ["vendor", 100],
    ]


@register_search
class MacAddressTableEntryIndex(SearchIndex):
    """Includes MacAddressTableEntry in global search."""

    model = MacAddressTableEntry
    fields = [
        ["mac_address", 100],
        ["vendor", 100],
    ]


@register_search
class RouteTableEntryIndex(SearchIndex):
    """Includes RouteTableEntry in global search."""

    model = RouteTableEntry
    fields = [
        ["destination", 100],
        ["nexthop_ip", 100],
    ]
