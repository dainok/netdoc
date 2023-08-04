"""Create CSV reports.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < automate_reports.py
"""
import csv

from django.db.models import Count

from dcim.models import Device, Site, DeviceRole, Interface
from ipam.models import VRF

from netdoc.models import Discoverable, RouteTableEntry

role_ids=[4, 23, 24, 22, 19, 20, 21]
bb_role_ids=[23, 24, 19, 20, 21]

# Interface list
header = [
    "Site",
    "Device",
    "Role",
    "Interface",
    "Type",
    "Enabled",
    "Description",
]
interface_qs = Interface.objects.filter(device__device_role_id__in=role_ids).order_by("device__site__name", "device__name", "name")
report_fh = open("report_interface_list.csv", "w", encoding="UTF8")
csv_writer = csv.writer(report_fh)
csv_writer.writerow(header)
for interface_o in interface_qs:
    lowercase_description = interface_o.description.lower()
    int_type = None
    if lowercase_description.startswith("vrf"):
        int_type = "vrf"
    if lowercase_description.startswith("pw"):
        int_type = "pw"
    if lowercase_description.startswith("vpls"):
        int_type = "vpls"
    if lowercase_description.endswith(":accesso"):
        int_type = "access"

    if int_type:
        csv_writer.writerow([
            interface_o.device.site.name,
            interface_o.device.name,
            interface_o.device.device_role.name,
            interface_o.name,
            int_type,
            interface_o.enabled,
            interface_o.description,
        ])
report_fh.close()

# Device count per site
header = [
    "Site",
    "Number of devices",
]
site_qs = Site.objects.filter(devices__device_role_id__in=role_ids).annotate(device_count=Count("devices")).filter(device_count__gt=0).order_by("name")
report_fh = open("report_site_list.csv", "w", encoding="UTF8")
csv_writer = csv.writer(report_fh)
csv_writer.writerow(header)
for site_o in site_qs:
    csv_writer.writerow([
        site_o.name,
        site_o.device_count,
    ])
report_fh.close()

# Device list ordered by site with discoverable IP address
header = [
    "Site",
    "Name",
    "Role",
    "Type",
    "Manufacturer",
    "Address",
]
device_qs = Device.objects.filter(device_role_id__in=role_ids).order_by("site__name")
report_fh = open("report_device_list.csv", "w", encoding="UTF8")
csv_writer = csv.writer(report_fh)
csv_writer.writerow(header)
for device_o in device_qs:
    try:
        discoverable_ip = Discoverable.objects.get(device__id=device_o.id).address
    except Discoverable.DoesNotExist:
        discoverable_ip = None
    csv_writer.writerow([
        device_o.site.name,
        device_o.name,
        device_o.device_role.name,
        device_o.device_type.model,
        device_o.device_type.manufacturer.name,
        discoverable_ip,
    ])
report_fh.close()

# Undiscoverable devices
header = [
    "Address",
]
discoverable_qs = Discoverable.objects.filter(last_discovered_at=None, discoverable=True).order_by("address")
report_fh = open("report_undiscoverable_list.csv", "w", encoding="UTF8")
csv_writer = csv.writer(report_fh)
csv_writer.writerow(header)
for discoverable_o in discoverable_qs:
    csv_writer.writerow([
        discoverable_o.address,
    ])
report_fh.close()

# Device/VRF/Routes count matrix
vrf_qs = VRF.objects.all().order_by("name")
vrf_list = list(vrf_qs.values_list("name", flat=True))
vrf_count = len(vrf_list)
header = ["Device \ VRF", "Global"] + vrf_list
device_qs = Device.objects.filter(device_role_id__in=bb_role_ids).order_by("name")
report_fh = open("report_device_vrf_routes_matrix.csv", "w", encoding="UTF8")
csv_writer = csv.writer(report_fh)
csv_writer.writerow(header)
for device_o in device_qs:
    vrf_fields = []
    route_qs = RouteTableEntry.objects.filter(device__name=device_o.name)
    if len(route_qs) == 0:
        # Not a router
        continue
    for vrf_o in vrf_qs:
        route_count = len(route_qs.filter(vrf_id=vrf_o.id))
        if route_count == 0:
            route_count = None
        vrf_fields.append(route_count)
    global_route_count = len(route_qs.filter(vrf_id=None))
    if not global_route_count:
        global_route_count = None
    csv_writer.writerow([device_o.name, global_route_count] + vrf_fields)
report_fh.close()
