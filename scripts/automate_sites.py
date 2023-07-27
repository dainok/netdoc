"""Create and assign sites based on device attributes.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < automate_sites.py
"""
from dcim.models import Device, Site, DeviceRole
from netdoc.models import Diagram

device_qs = Device.objects.all()
for device_o in device_qs:
    site_name = device_o.name.split("-")[0]
    site_slug = site_name.lower()
    diagram_name = f"Site {site_name}"
    try:
        print("Looking for site ", site_slug)
        site_o = Site.objects.get(slug=site_slug)
    except Site.DoesNotExist:
        print("Creating site ", site_name)
        site_o = Site.objects.create(name=site_name, slug=site_slug)
    if device_o.site.pk != site_o.pk:
        print("Update site on ", device_o.name)
        device_o.site = site_o
        device_o.save()

    if "-ME36-" in device_o.name:
        role_o = DeviceRole.objects.get(slug="access-switch")
        if device_o.device_role.pk != role_o.pk:
            print("Update role on ", device_o.name)
            device_o.device_role = role_o
            device_o.save()
    if "-ME38-" in device_o.name or "-A9k" in device_o.name:
        role_o = DeviceRole.objects.get(slug="router")
        if device_o.device_role.pk != role_o.pk:
            print("Update role on ", device_o.name)
            device_o.device_role = role_o
            device_o.save()

    # Create site diagram
    diagram_o, created = Diagram.objects.get_or_create(name=diagram_name, mode="l2")
    if created:
        diagram_o.sites.add(site_o)
