"""Delete duplicated Prefixes.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < del_duplicated_prefixes.py
"""
from django.db.models import Count

from ipam.models import Prefix

duplicated_prefix_ids = []
prefix_qs = (
    Prefix.objects.values("prefix", "vrf")
    .annotate(prefix_count=Count("prefix"))
    .filter(prefix_count__gte=2)
)
for prefix in prefix_qs:
    duplicated_prefix_qs = list(Prefix.objects.filter(
        vrf=prefix.get("vrf"),
        prefix=prefix.get("prefix"),
    ).values_list("id", flat=True))[1:]
    duplicated_prefix_ids.extend(duplicated_prefix_qs)

count = Prefix.objects.filter(id__in=duplicated_prefix_ids).delete()
print(f"Deleted {count[0]} duplicated Prefixes")
