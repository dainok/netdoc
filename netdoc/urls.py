"""URLs."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from django.urls import path

from netbox.views.generic import ObjectChangeLogView
from netdoc import models, views


urlpatterns = (
    #
    # ARPEntry urls
    #
    path("arptable/", views.ArpTableListView.as_view(), name="arptableentry_list"),
    path("arptable/<int:pk>/", views.ArpTableView.as_view(), name="arptableentry"),
    #
    # Credential urls
    #
    path("credential/", views.CredentialListView.as_view(), name="credential_list"),
    path("credential/add/", views.CredentialEditView.as_view(), name="credential_add"),
    path(
        "credential/import/",
        views.CredentialBulkImportView.as_view(),
        name="credential_import",
    ),
    path(
        "credential/edit/",
        views.CredentialBulkEditView.as_view(),
        name="credential_bulk_edit",
    ),
    path(
        "credential/delete/",
        views.CredentialBulkDeleteView.as_view(),
        name="credential_bulk_delete",
    ),
    path("credential/<int:pk>/", views.CredentialView.as_view(), name="credential"),
    path(
        "credential/<int:pk>/edit/",
        views.CredentialEditView.as_view(),
        name="credential_edit",
    ),
    path(
        "credential/<int:pk>/delete/",
        views.CredentialDeleteView.as_view(),
        name="credential_delete",
    ),
    path(
        "credential/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="credential_changelog",
        kwargs={"model": models.Credential},
    ),
    #
    # Diagram urls
    #
    path("diagram/", views.DiagramListView.as_view(), name="diagram_list"),
    path("diagram/add/", views.DiagramEditView.as_view(), name="diagram_add"),
    path("diagram/<int:pk>/", views.DiagramView.as_view(), name="diagram"),
    path(
        "diagram/<int:pk>/edit/",
        views.DiagramEditView.as_view(),
        name="diagram_edit",
    ),
    path(
        "diagram/<int:pk>/export/",
        views.DiagramExportView.as_view(),
        name="diagram_export",
    ),
    path(
        "diagram/<int:pk>/delete/",
        views.DiagramDeleteView.as_view(),
        name="diagram_delete",
    ),
    path(
        "diagram/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="diagram_changelog",
        kwargs={"model": models.Diagram},
    ),
    #
    # Discoverable urls
    #
    path(
        "discoverable/", views.DiscoverableListView.as_view(), name="discoverable_list"
    ),
    path(
        "discoverable/add/",
        views.DiscoverableEditView.as_view(),
        name="discoverable_add",
    ),
    path(
        "discoverable/import/",
        views.DiscoverableBulkImportView.as_view(),
        name="discoverable_import",
    ),
    path(
        "discoverable/edit/",
        views.DiscoverableBulkEditView.as_view(),
        name="discoverable_bulk_edit",
    ),
    path(
        "discoverable/delete/",
        views.DiscoverableBulkDeleteView.as_view(),
        name="discoverable_bulk_delete",
    ),
    path(
        "discoverable/discover/",
        views.DiscoverableBulkDiscoverView.as_view(),
        name="discoverable_bulk_discover",
    ),
    path(
        "discoverable/<int:pk>/", views.DiscoverableView.as_view(), name="discoverable"
    ),
    path(
        "discoverable/<int:pk>/edit/",
        views.DiscoverableEditView.as_view(),
        name="discoverable_edit",
    ),
    path(
        "discoverable/<int:pk>/delete/",
        views.DiscoverableDeleteView.as_view(),
        name="discoverable_delete",
    ),
    path(
        "discoverable/<int:pk>/discover/",
        views.DiscoverableDiscoverView.as_view(),
        name="discoverable_discover",
    ),
    path(
        "discoverable/<int:pk>/changelog/",
        ObjectChangeLogView.as_view(),
        name="discoverable_changelog",
        kwargs={"model": models.Discoverable},
    ),
    #
    # DiscoveryLog urls
    #
    path(
        "discoverylog/", views.DiscoveryLogListView.as_view(), name="discoverylog_list"
    ),
    path(
        "discoverylog/delete/",
        views.DiscoveryLogBulkDeleteView.as_view(),
        name="discoverylog_bulk_delete",
    ),
    path(
        "discoverylog/<int:pk>/", views.DiscoveryLogView.as_view(), name="discoverylog"
    ),
    path(
        "discoverylog/<int:pk>/export/",
        views.DiscoveryLogExportView.as_view(),
        name="discoverylog_export",
    ),
    path(
        "discoverylog/<int:pk>/delete/",
        views.DiscoveryLogDeleteView.as_view(),
        name="discoverylog_delete",
    ),
    #
    # MacAddressTableEntry urls
    #
    path(
        "macaddresstable/",
        views.MacAddressTableListView.as_view(),
        name="macaddresstableentry_list",
    ),
    path(
        "macaddresstable/<int:pk>/",
        views.MacAddressTableView.as_view(),
        name="macaddresstableentry",
    ),
    #
    # RoutingTableEntry urls
    #
    path(
        "routingtable/",
        views.RouteTableEntryListView.as_view(),
        name="routetableentry_list",
    ),
    path(
        "routingtable/<int:pk>/",
        views.RouteTableEntryView.as_view(),
        name="routetableentry",
    ),
)
