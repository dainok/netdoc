"""Delete dupplicated IPAddresses.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < del_duplicated_ip_addresses.py
"""
from django.db.models import Count

from ipam.models import IPAddress

duplicated_ip_address_ids = []
ip_address_qs = (
    IPAddress.objects.values("address", "vrf", "assigned_object_id")
    .annotate(address_count=Count("address"))
    .filter(address_count__gte=2)
)
for ip_address in ip_address_qs:
    duplicated_ip_address_qs = list(IPAddress.objects.filter(
        vrf=ip_address.get("vrf"),
        assigned_object_id=ip_address.get("assigned_object_id"),
        address=ip_address.get("address"),
    ).values_list("id", flat=True))[1:]
    duplicated_ip_address_ids.extend(duplicated_ip_address_qs)

count = IPAddress.objects.filter(id__in=duplicated_ip_address_ids).delete()
print(f"Deleted {count[0]} duplicated IPAddresses")
