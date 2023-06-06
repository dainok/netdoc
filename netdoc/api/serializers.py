"""Serializers, called by API Views for add/ediit actions."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from rest_framework import serializers

from netbox.api.serializers import NetBoxModelSerializer

from netdoc.models import (
    Credential,
    Discoverable,
    DiscoveryLog,
    RouteTableEntry,
    ArpTableEntry,
    MacAddressTableEntry,
    Diagram,
)


class ArpTableEntrySerializer(NetBoxModelSerializer):
    """Serializer to validate ArpTableEntry data.

    No need to view-details/edit/delete, so url and View are missing.
    """

    class Meta:
        """Serializer metadata."""

        model = ArpTableEntry
        fields = "__all__"


class CredentialSerializer(NetBoxModelSerializer):
    """Serializer to validate Credential data."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netdoc-api:credential-detail"
    )
    discoverables_count = serializers.IntegerField(read_only=True)

    class Meta:
        """Serializer metadata."""

        model = Credential
        fields = "__all__"


class DiagramSerializer(NetBoxModelSerializer):
    """Serializer to validate Diagram data."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netdoc-api:diagram-detail"
    )
    discoverables_count = serializers.IntegerField(read_only=True)

    class Meta:
        """Serializer metadata."""

        model = Diagram
        fields = "__all__"


class DiscoverableSerializer(NetBoxModelSerializer):
    """Serializer to validate Discoverable data."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netdoc-api:discoverable-detail"
    )

    class Meta:
        """Serializer metadata."""

        model = Discoverable
        fields = "__all__"


class DiscoveryLogSerializer(NetBoxModelSerializer):
    """Serializer to validate DiscoveryLog data."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netdoc-api:discoverylog-detail"
    )

    class Meta:
        """Serializer metadata."""

        model = DiscoveryLog
        fields = "__all__"


class MacAddressTableEntrySerializer(NetBoxModelSerializer):
    """Serializer to validate MacAddressTableEntry data.

    No need to view-details/edit/delete, so url and View are missing.
    """

    class Meta:
        """Serializer metadata."""

        model = MacAddressTableEntry
        fields = "__all__"


class RouteTableEntrySerializer(NetBoxModelSerializer):
    """Serializer to validate RouteTableEntry data.

    No need to view-details/edit/delete, so url and View are missing.
    """

    class Meta:
        """Serializer metadata."""

        model = RouteTableEntry
        fields = "__all__"
