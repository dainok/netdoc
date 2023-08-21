"""Ingestor for netmiko_cisco_ios_show_ip_route."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import interface, vrf, routetableentry
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device
    vrf_name = utils.normalize_vrf_name(log.details.get("vrf"))

    # Get or create VRF
    vrf_o = None
    if vrf_name:
        vrf_o = vrf.get_or_create(name=vrf_name)[0]

    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/cisco_ios/show_ip_route # pylint: disable=line-too-long
        nexthop_if_name = item.get("nexthop_if")
        distance = int(item.get("distance")) if item.get("distance") else None
        metric = int(item.get("metric")) if item.get("metric") else None
        destination = (
            f"{item.get('network')}/{item.get('prefix_length')}"
            if item.get("network")
            else None
        )
        protocol = utils.normalize_route_type(item.get("protocol"))
        nexthop_ip = item.get("nexthop_ip") if item.get("nexthop_ip") else None
        if not nexthop_if_name and not nexthop_ip:
            # Skipping routes without nexthop IP / interface
            continue

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
