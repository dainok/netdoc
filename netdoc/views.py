"""Views, called by URLs."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import logging
import json

from django.db.models import Count
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse

from utilities.forms import ConfirmationForm
from utilities.htmx import is_htmx
from utilities.permissions import get_permission_for_model
from utilities.utils import get_viewname
from netbox.views import generic

from netdoc import models, tables, forms, filtersets, utils, topologies

#
# ARPEntry views
#


class ArpTableListView(generic.ObjectListView):
    """Summary view listing all ARP."""

    queryset = models.ArpTableEntry.objects.all().order_by(
        "interface__device__name", "interface__name", "ip_address"
    )
    table = tables.ArpTableEntryTable
    filterset = filtersets.ArpTableEntryFilterSet
    actions = [
        "export",
    ]


class ArpTableView(generic.ObjectView):
    """Detailed ARP table entry view."""

    queryset = models.ArpTableEntry.objects.all()

    def get_extra_context(self, request, instance):
        """Get associated ARP and MAC Address tables."""
        arp_table_qs = models.ArpTableEntry.objects.filter(
            ip_address=str(instance.ip_address)
        )
        arp_table = tables.ArpTableEntryTable(arp_table_qs)
        arp_table.configure(request)

        macaddress_table_qs = models.MacAddressTableEntry.objects.filter(
            mac_address=instance.mac_address
        )
        macaddress_table = tables.MacAddressTableEntryTable(macaddress_table_qs)
        macaddress_table.configure(request)

        return {
            "arp_table": arp_table,
            "macaddress_table": macaddress_table,
        }


#
# Credential views
#


class CredentialListView(generic.ObjectListView):
    """Summary view listing all Credential objects."""

    queryset = models.Credential.objects.annotate(
        discoverables_count=Count("discoverables")
    ).order_by("name")
    table = tables.CredentialTable
    filterset = filtersets.CredentialFilterSet
    actions = [
        "add",
        "import",
        "bulk_delete",
    ]


class CredentialView(generic.ObjectView):
    """Detailed Credential view."""

    queryset = models.Credential.objects.all()

    def get_extra_context(self, request, instance):
        """Get associated Discoverable obhects."""
        table = tables.DiscoverableTableWOLogCount(instance.discoverables.all())
        table.configure(request)

        return {
            "discoverables_table": table,
        }


class CredentialEditView(generic.ObjectEditView):
    """Edit Credential view."""

    queryset = models.Credential.objects.all()
    form = forms.CredentialForm


class CredentialDeleteView(generic.ObjectDeleteView):
    """Delete Credential view."""

    queryset = models.Credential.objects.all()
    default_return_url = "plugins:netdoc:credential_list"


class CredentialBulkImportView(generic.BulkImportView):
    """Bulk import Credential view."""

    queryset = models.Credential.objects.all()
    model_form = forms.CredentialCSVForm
    table = tables.CredentialTable


class CredentialBulkEditView(generic.BulkEditView):
    """Bulk edit Credential view."""

    queryset = models.Credential.objects.all()
    table = tables.CredentialTable
    default_return_url = "plugins:netdoc:credential_list"
    filterset = filtersets.CredentialFilterSet


class CredentialBulkDeleteView(generic.BulkDeleteView):
    """Bulk delete Credential view."""

    queryset = models.Credential.objects.all()
    table = tables.CredentialTable
    default_return_url = "plugins:netdoc:credential_list"
    filterset = filtersets.CredentialFilterSet


#
# Diagram views
#


class DiagramListView(generic.ObjectListView):
    """Summary view listing all Diagram objects."""

    queryset = models.Diagram.objects.all().order_by("name")
    table = tables.DiagramTable


class DiagramView(generic.ObjectView):
    """Detailed Diagram view."""

    queryset = models.Diagram.objects.all()

    def get_extra_context(self, request, instance):
        """Get associated Diagram obhects from Interface queryset."""
        sites = list(instance.sites.all().values_list("id", flat=True))
        roles = list(instance.device_roles.all().values_list("id", flat=True))
        vrfs = list(instance.vrfs.all().values_list("id", flat=True))

        interface_qs = utils.get_diagram_interfaces(
            instance.mode,
            sites=sites,
            roles=roles,
            vrfs=vrfs,
            include_global_vrf=instance.include_global_vrf,
        )

        # Build and return the topology
        try:
            module = getattr(topologies, f"get_{instance.mode}_topology_data")
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                f"Get topology function not found for {instance.mode}"
            ) from exc
        return {
            "topology_data": module(interface_qs, instance.details),
            "topology_details": instance.details,
        }


class DiagramEditView(generic.ObjectEditView):
    """Edit Diagram view."""

    queryset = models.Diagram.objects.all()
    form = forms.DiagramForm


class DiagramDeleteView(generic.ObjectDeleteView):
    """Delete Diagram view."""

    queryset = models.Diagram.objects.all()
    default_return_url = "plugins:netdoc:diagram_list"


class DiagramExportView(generic.ObjectDeleteView):
    """
    Export a single object.

    Called from:
    * DiagramView clicking on the Export button on a specific Diagram.
    """

    queryset = models.Diagram.objects.all()

    def get(self, request, *args, **kwargs):
        """Download the log."""
        instance = self.get_object(**kwargs)
        sites = list(instance.sites.all().values_list("id", flat=True))
        roles = list(instance.device_roles.all().values_list("id", flat=True))
        vrfs = list(instance.vrfs.all().values_list("id", flat=True))

        interface_qs = utils.get_diagram_interfaces(
            instance.mode,
            sites=sites,
            roles=roles,
            vrfs=vrfs,
            include_global_vrf=instance.include_global_vrf,
        )

        # Build and return the topology
        try:
            module = getattr(topologies, f"get_{instance.mode}_drawio_topology")
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                f"Get DrawIO topology function not found for {instance.mode}"
            ) from exc
        drawio_xml = module(interface_qs, instance)

        response = HttpResponse(drawio_xml, content_type="application/xml")
        response["Content-Disposition"] = f"attachment; filename={instance.name}.drawio"
        return response


#
# Discoverable views
#


class DiscoverableListView(generic.ObjectListView):
    """Summary view listing all Discoverable objects."""

    queryset = models.Discoverable.objects.annotate(
        discoverylogs_count=Count("discoverylogs")
    ).order_by("device__name", "address")
    table = tables.DiscoverableTable
    actions = [
        "add",
        "import",
        "export",
        "discover",
        "bulk_edit",
        "bulk_delete",
        "bulk_discover",
    ]
    template_name = "netdoc/discoverable_list.html"
    filterset = filtersets.DiscoverableFilterSet
    filterset_form = forms.DiscoverableListFilterForm


class DiscoverableView(generic.ObjectView):
    """Detailed Discoverable view."""

    queryset = models.Discoverable.objects.annotate(
        discoverylogs_count=Count("discoverylogs")
    )

    def get_extra_context(self, request, instance):
        """Get associated DiscoveryLog obhects."""
        table = tables.DiscoveryLogTable(
            instance.discoverylogs.all().order_by("-created")
        )
        table.configure(request)

        return {
            "discoverylogs_table": table,
        }


class DiscoverableEditView(generic.ObjectEditView):
    """Edit Discoverable view."""

    queryset = models.Discoverable.objects.all()
    form = forms.DiscoverableForm


class DiscoverableDeleteView(generic.ObjectDeleteView):
    """Delete Discoverable view."""

    queryset = models.Discoverable.objects.all()
    default_return_url = "plugins:netdoc:discoverable_list"


class DiscoverableBulkImportView(generic.BulkImportView):
    """Bulk import Discoverable view."""

    queryset = models.Discoverable.objects.all()
    model_form = forms.DiscoverableCSVForm
    table = tables.DiscoverableTable


class DiscoverableBulkEditView(generic.BulkEditView):
    """Bulk edit Discoverable view."""

    queryset = models.Discoverable.objects.all()
    table = tables.DiscoverableTable
    form = forms.DiscoverableBulkEditForm


class DiscoverableBulkDeleteView(generic.BulkDeleteView):
    """Bulk delete Discoverable view."""

    queryset = models.Discoverable.objects.all()
    table = tables.DiscoverableTable
    default_return_url = "plugins:netdoc:discoverable_list"


class DiscoverableDiscoverView(generic.ObjectDeleteView):
    """
    Discover a single object.

    Called from:
    * DiscoverableListView clicking on the Discovery button on a specific Discoverable row.
    * DiscoverableView clicking on the Discovery button.
    """

    queryset = models.Discoverable.objects.all()
    template_name = "netdoc/discoverable_discover.html"

    def get_required_permission(self):
        """Check permissions."""
        return get_permission_for_model(self.queryset.model, "change")

    #
    # Request handlers
    #

    def get(self, request, *args, **kwargs):
        """Return the confirmation page."""
        obj = self.get_object(**kwargs)
        form = ConfirmationForm(initial=request.GET)

        # If this is an HTMX request, return only the rendered deletion form as modal content
        if is_htmx(request):
            # Called from DiscoverableView
            viewname = get_viewname(self.queryset.model, action="discover")
            form_url = reverse(viewname, kwargs={"pk": obj.pk})
            return render(
                request,
                "netdoc/htmx/discover_form.html",
                {
                    "object": obj,
                    "object_type": self.queryset.model._meta.verbose_name,  # pylint: disable=protected-access
                    "form": form,
                    "form_url": form_url,
                    **self.get_extra_context(request, obj),
                },
            )

        # Called from DiscoverableViewList
        return render(
            request,
            self.template_name,
            {
                "object": obj,
                "form": form,
                "return_url": self.get_return_url(request, obj),
                **self.get_extra_context(request, obj),
            },
        )

    def post(self, request, *args, **kwargs):
        """Start the discovery on a single Discoverable."""
        logger = logging.getLogger("netbox.plugins.netdoc")
        obj = self.get_object(**kwargs)
        form = ConfirmationForm(request.POST)

        if form.is_valid():
            logger.debug("Form validation was successful")
            discoverables = [obj]

            # Starting discovery job on default queue (single Discoverable)
            msg = f"Starting discovery on {obj}"
            logger.info(msg)
            messages.success(request, msg)
            data = {
                "discoverables": discoverables,
            }
            utils.spawn_script("Discover", user=request.user, post_data=data)

            # return_url = form.cleaned_data.get("return_url")
            # if return_url and return_url.startswith("/"):
            #     return redirect(return_url)
            return redirect(self.get_return_url(request, obj))

        logger.debug("Form validation failed")

        return render(
            request,
            self.template_name,
            {
                "object": obj,
                "form": form,
                "return_url": self.get_return_url(request, obj),
                **self.get_extra_context(request, obj),
            },
        )


class DiscoverableBulkDiscoverView(generic.BulkDeleteView):
    """
    Disocver devices in bulk.

    Called from:
    * DiscoverableListView selecting Discoverable(s) and clicking on Disocver Selected button.
    """

    template_name = "netdoc/discoverable_bulk_discover.html"
    queryset = models.Discoverable.objects.prefetch_related("credential")
    filterset = None
    table = tables.DiscoverableTable
    default_return_url = "plugins:netdoc:discoverable_list"

    def get_required_permission(self):
        """Check permissions."""
        return get_permission_for_model(self.queryset.model, "change")

    def post(self, request, **kwargs):
        """Start the discovery."""
        logger = logging.getLogger("netbox.plugins.netdoc")
        model = self.queryset.model

        # Are we discovering *all* objects in the queryset or just a selected subset?
        if request.POST.get("_all"):
            queryset = model.objects.all()
            pk_list = queryset.only("pk").values_list("pk", flat=True)
        else:
            pk_list = [int(pk) for pk in request.POST.getlist("pk")]

        form_cls = self.get_form()

        if "_confirm" in request.POST:
            form = form_cls(request.POST)
            if form.is_valid():
                logger.debug("Form validation was successful")
                queryset = self.queryset.filter(pk__in=pk_list)
                discovery_count = queryset.count()

                # Starting discovery job on default queue (list of Discoverable)
                msg = f"Starting discovery on {discovery_count} {model._meta.verbose_name_plural}"  # pylint: disable=protected-access
                logger.info(msg)
                messages.success(request, msg)
                data = {
                    "discoverables": list(queryset),
                }
                utils.spawn_script("Discover", user=request.user, post_data=data)

                return redirect(self.get_return_url(request))

            logger.debug("Form validation failed")

        else:
            form = form_cls(
                initial={
                    "pk": pk_list,
                    "return_url": self.get_return_url(request),
                }
            )

        # Retrieve objects being deleted
        table = self.table(self.queryset.filter(pk__in=pk_list), orderable=False)
        if not table.rows:
            messages.warning(
                request,
                f"No {model._meta.verbose_name_plural} were selected for discovery.",  # pylint: disable=protected-access
            )
            return redirect(self.get_return_url(request))

        return render(
            request,
            self.template_name,
            {
                "model": model,
                "form": form,
                "table": table,
                "return_url": self.get_return_url(request),
                **self.get_extra_context(request),
            },
        )


#
# DiscoveryLog views
#


class DiscoveryLogListView(generic.ObjectListView):
    """Summary view listing all DiscoveryLog objects."""

    queryset = models.DiscoveryLog.objects.all().order_by("-created")
    table = tables.DiscoveryLogTable
    filterset = filtersets.DiscoveryLogFilterSet
    filterset_form = forms.DiscoveryLogListFilterForm
    actions = ["delete", "bulk_delete"]  # Read-only + delete + bulk-delete delete


class DiscoveryLogView(generic.ObjectView):
    """Detailed DiscoveryLog view."""

    queryset = models.DiscoveryLog.objects.all()


class DiscoveryLogDeleteView(generic.ObjectDeleteView):
    """Delete DiscoveryLog view."""

    queryset = models.DiscoveryLog.objects.all()
    default_return_url = "plugins:netdoc:discoverylog_list"


class DiscoveryLogExportView(generic.ObjectView):
    """
    Export a single object.

    Called from:
    * DiscoveryLogView clicking on the Discovery button on a specific Discoverable.
    """

    queryset = models.DiscoveryLog.objects.all()

    def get(self, request, **kwargs):
        """Download the log."""
        instance = self.get_object(**kwargs)
        data = utils.export_log(instance)
        response = HttpResponse(json.dumps(data), content_type="application/json")
        response["Content-Disposition"] = f"attachment; filename={instance.id}.json"
        return response


class DiscoveryLogBulkDeleteView(generic.BulkDeleteView):
    """Bulk delete DiscoveryLog view."""

    queryset = models.DiscoveryLog.objects.all()
    table = tables.DiscoveryLogTable
    default_return_url = "plugins:netdoc:discoverylog_list"


#
# MacAddressTableEntry views
#


class MacAddressTableListView(generic.ObjectListView):
    """Summary view listing all MAC address."""

    queryset = models.MacAddressTableEntry.objects.all().order_by(
        "interface__device__name", "interface__name", "mac_address"
    )
    table = tables.MacAddressTableEntryTable
    filterset = filtersets.MacAddressTableEntryFilterSet
    actions = [
        "export",
    ]


class MacAddressTableView(generic.ObjectView):
    """Detailed MAC address entry view."""

    queryset = models.MacAddressTableEntry.objects.all()
    actions = []  # Read only table

    def get_extra_context(self, request, instance):
        """Get associated MAC Address tables."""
        arp_table_qs = models.ArpTableEntry.objects.filter(
            mac_address=str(instance.mac_address)
        )
        arp_table = tables.ArpTableEntryTable(arp_table_qs)
        arp_table.configure(request)

        macaddress_table_qs = models.MacAddressTableEntry.objects.filter(
            mac_address=instance.mac_address
        )
        macaddress_table = tables.MacAddressTableEntryTable(macaddress_table_qs)
        macaddress_table.configure(request)

        return {
            "arp_table": arp_table,
            "macaddress_table": macaddress_table,
        }


#
# RouteTableEntry view
#


class RouteTableEntryListView(generic.ObjectListView):
    """Summary view listing all routes."""

    queryset = models.RouteTableEntry.objects.all().order_by(
        "device__name", "destination", "protocol", "nexthop_if__name"
    )
    table = tables.RouteTableEntryTable
    filterset = filtersets.RouteTableEntryFilterSet
    actions = [
        "export",
    ]


class RouteTableEntryView(generic.ObjectView):
    """Detailed route table entry view."""

    queryset = models.RouteTableEntry.objects.all()
    actions = []  # Read only table
