"""Create CSV reports.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < automate_reports.py
"""
import csv

from django.db.models import Count

from dcim.models import Device, Site, DeviceRole

from netdoc.models import Discoverable

# Device count per site
header = [
    "Site",
    "Number of devices",
]
site_qs = Site.objects.all().annotate(device_count=Count("devices")).order_by("name")
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
device_qs = Device.objects.all().order_by("site__name")
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

