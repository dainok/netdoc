"""Ingestor for xml_panw_ngfw_show_arp."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2023, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import (
    interface,
    virtualmachine_interface,
    vrf,
    routetableentry,
)
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    device_o = log.discoverable.device if log.discoverable.device else None
    vm_o = log.discoverable.vm if log.discoverable.vm else None

    try:
        items = log.parsed_output.get("response").get("result").get("entry")
    except AttributeError:
        items = []
    for item in items:
        flags = item.get("flags")
        if not flags.startswith("A"):
            # Only keep active routes
            continue
        nexthop_if_name = item.get("interface")
        vrf_name = utils.normalize_vrf_name(item.get("virtual-router"))
        metric = int(item.get("metric")) if item.get("metric") else None
        destination = item.get("destination")
        protocol = utils.normalize_route_type(item.get("flags"))
        nexthop_ip = item.get("nexthop")

        # Get or create VRF
        vrf_o = None
        if vrf_name:
            vrf_o = vrf.get_or_create(name=vrf_name)[0]

        if vm_o:
            # Get or create interface
            nexthop_if_id = None
            if nexthop_if_name:
                nexthop_if_o = virtualmachine_interface.get(
                    virtual_machine_id=vm_o.id, name=nexthop_if_name
                )
                if not nexthop_if_o:
                    # Skip inter-VRF leaking
                    continue
                nexthop_if_id = nexthop_if_o.id

            # Get or create route table entry
            routetableentry_o = routetableentry.get(
                vm_id=vm_o.id,
                destination=destination,
                metric=metric,
                protocol=protocol,
                nexthop_virtual_if_id=nexthop_if_id,
                nexthop_ip=nexthop_ip,
            )
            if not routetableentry_o:
                data = {
                    "vm_id": vm_o.id,
                    "destination": destination,
                    "metric": metric,
                    "protocol": protocol,
                    "nexthop_virtual_if_id": nexthop_if_id,
                    "nexthop_ip": nexthop_ip,
                    "vrf_id": vrf_o.id if vrf_o else None,
                }

                routetableentry.create(**data)

        if device_o:
            # Get or create interface
            nexthop_if_label = utils.normalize_interface_label(nexthop_if_name)
            nexthop_if_id = None
            if nexthop_if_name:
                nexthop_if_o = interface.get(
                    device_id=device_o.id, label=nexthop_if_label
                )
                if not nexthop_if_o:
                    # Skip inter-VRF leaking
                    continue
                nexthop_if_id = nexthop_if_o.id

            # Get or create route table entry
            routetableentry_o = routetableentry.get(
                device_id=device_o.id,
                destination=destination,
                metric=metric,
                protocol=protocol,
                nexthop_if_id=nexthop_if_id,
                nexthop_ip=nexthop_ip,
            )
            if not routetableentry_o:
                data = {
                    "device_id": device_o.id,
                    "destination": destination,
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
