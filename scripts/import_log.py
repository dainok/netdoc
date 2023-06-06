"""Import exported DiscoveryLogs.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < import_log.py
"""
from os import walk
import sys
import json

from netdoc.models import Discoverable
from netdoc.schemas import discoverylog

files = []

for dirpath, dirnames, filenames in walk("."):
    for filename in filenames:
        if filename.endswith(".json"):
            files.append(filename)

for file in files:
    print(f"Importing {file}")
    with open(file, "r", encoding="utf-8") as metadata_fh:
        discoverablelog_json = json.load(metadata_fh)

    discoverable_qs = Discoverable.objects.filter(
        mode=discoverablelog_json["discoverable__mode"]
    )
    mode = discoverablelog_json["discoverable__mode"]
    del discoverablelog_json["discoverable__mode"]
    if discoverable_qs:
        discoverable_o = discoverable_qs.first()
    else:
        print(f"Create a Discoverable with mode {mode} before importing")
        sys.exit()

    discoverylog.create(discoverable_id=discoverable_o.id, **discoverablelog_json)
