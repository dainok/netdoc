"""API View, called by API URLs."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netbox.api.viewsets import NetBoxModelViewSet

from netdoc import models
from netdoc.api.serializers import (
    CredentialSerializer,
    DiscoverableSerializer,
    DiscoveryLogSerializer,
    DiagramSerializer,
)


class CredentialViewSet(NetBoxModelViewSet):
    """API View for add/edit Credential."""

    queryset = models.Credential.objects.prefetch_related("tags")
    serializer_class = CredentialSerializer


class DiagramViewSet(NetBoxModelViewSet):
    """API View for add/edit Diagram."""

    queryset = models.Diagram.objects.prefetch_related("tags")
    serializer_class = DiagramSerializer


class DiscoverableViewSet(NetBoxModelViewSet):
    """API View for add/edit Discoverable."""

    queryset = models.Discoverable.objects.prefetch_related("tags")
    serializer_class = DiscoverableSerializer


class DiscoveryLogViewSet(NetBoxModelViewSet):
    """API View for add/edit DiscoveryLog."""

    queryset = models.DiscoveryLog.objects.prefetch_related("tags")
    serializer_class = DiscoveryLogSerializer
