"""Ingestor for netmiko_hp_procurve_show_ip_route."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

import ipaddress

from netdoc.schemas import interface, routetableentry
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device

    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/hp_procurve/show_ip_route # pylint: disable=line-too-long
        nexthop = item.get("gateway")
        if not nexthop:
            # Skip routes with no nexthop (interface or IP address)
            continue
        try:
            nexthop_ip = str(ipaddress.IPv4Address(item.get("gateway")))
            nexthop_if_name = None
        except ipaddress.AddressValueError:
            nexthop_ip = None
            nexthop_if_name = item.get("gateway")
        distance = int(item.get("distance")) if item.get("distance") else None
        metric = int(item.get("metric")) if item.get("metric") else None
        destination = item.get("destination") if item.get("destination") else None
        protocol = utils.normalize_route_type(item.get("type"))

        # Get or create interface
        nexthop_if_id = None
        if nexthop_if_name:
            nexthop_if_label = utils.normalize_interface_label(nexthop_if_name)
            nexthop_if_o = interface.get(device_id=device_o.id, label=nexthop_if_label)
            if not nexthop_if_o:
                interface_data = {
                    "name": nexthop_if_label,
                    "device_id": device_o.id,
                }
                nexthop_if_o = interface.create(**interface_data)
            nexthop_if_id = nexthop_if_o.id

        # Get or create route table entry
        routetableentry_o = routetableentry.get(
            device_id=device_o.id,
            destination=destination,
            distance=distance,
            metric=metric,
            protocol=protocol,
            nexthop_if_id=nexthop_if_id,
            nexthop_ip=nexthop_ip,
        )
        if not routetableentry_o:
            data = {
                "device_id": device_o.id,
                "destination": destination,
                "distance": distance,
                "metric": metric,
                "protocol": protocol,
                "nexthop_if_id": nexthop_if_id,
                "nexthop_ip": nexthop_ip,
            }

            routetableentry.create(**data)

    # Update the log
    log.ingested = True
    log.save()
