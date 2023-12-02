"""Ingestor for netmiko_huawei_vrf_display_vlan."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import vlan


def ingest(log):
    """Processing parsed output.

    VLAN - Interface association is ingested in the "show interface switchport" output.
    """
    # See https://github.com/networktocode/ntc-templates/tree/master/tests/huawei_vrf/display_vlan # pylint: disable=line-too-long
    for item in log.parsed_output:
        # First loop -> add VLANs
        vlan_id = int(item.get("vlan_id"))
        vlan_name = item.get("vlan_name")

        if vlan_name:
            vlan_o = vlan.get(vlan_id, vlan_name)
            if not vlan_o:
                data = {
                    "name": vlan_name,
                    "vid": vlan_id,
                }
                vlan_o = vlan.create(**data)

    # Update the log
    log.ingested = True
    log.save()
