"""Import exported DiscoveryLogs.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < export_log.py
"""
from os import makedirs
import json

from netdoc.models import DiscoveryLog
from netdoc.utils import export_log

LAB = "lab1"

# Don't edit below this line

discoverylog_qs = DiscoveryLog.objects.all()
for discoverylog_o in discoverylog_qs:
    data = export_log(discoverylog_o)
    address = discoverylog_o.discoverable.address
    mode = discoverylog_o.discoverable.mode
    lab_path = f"netdoc/tests/{mode}/{LAB}"
    log_name = discoverylog_o.command.replace(" ", "_").replace("_|_", "_")
    raw_output = data.get("raw_output")

    # Reset data
    data["raw_output"] = ""
    data["parsed_output"] = ""
    data["parsed"] = False
    data["ingested"] = False
    data["success"] = True

    # Create directory
    makedirs(lab_path, exist_ok=True)
    makedirs(f"{lab_path}/logs", exist_ok=True)

    # Dump log
    with open(
        f"{lab_path}/logs/{address}-{log_name}.json", "w", encoding="utf-8"
    ) as fh:
        fh.write(json.dumps(data, indent=4, sort_keys=True))
    # Dump raw output
    with open(f"{lab_path}/logs/{address}-{log_name}.raw", "w", encoding="utf-8") as fh:
        fh.write(raw_output)
