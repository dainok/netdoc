"""Ingestor for netmiko_allied_telesis_show_ip_route."""
__remodeler__ = "tatumi0726"
__contact__ = "tatumi0726@gmail.com"
__copyright__ = "Copyright 2023, tatumi0726"
__license__ = "GPLv3"

from netdoc.schemas import interface, vrf, routetableentry
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device
    vrf_name = log.details.get("vrf")

    # Get or create VRF
    vrf_o = None
    if vrf_name:
        vrf_o = vrf.get(name=vrf_name)
        if not vrf_o:
            data = {
                "name": vrf_name,
            }
            vrf_o = vrf.create(**data)

    for item in log.parsed_output:
        nexthop_if_name = item.get("nexthop_if")
        distance = int(item.get("distance")) if item.get("distance") else None
        metric = int(item.get("metric")) if item.get("metric") else None
        destination = (
            f"{item.get('network')}/{item.get('mask')}" if item.get("network") else None
        )
        protocol = utils.normalize_route_type(item.get("protocol"))
        nexthop_ip = item.get("nexthop_ip") if item.get("nexthop_ip") else None

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
                "vrf_id": vrf_o.id if vrf_o else None,
            }

            routetableentry.create(**data)

    # Update the log
    log.ingested = True
    log.save()
