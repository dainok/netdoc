"""Ingestor for netmiko_allied_telesis_show_vlan_all."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2024, Andrea Dainese"
__license__ = "GPLv3"


from netdoc.schemas import vlan


def ingest(log):
    """Processing parsed output.

    VLAN - Interface association is ingested in the "show interface switchport" output.
    """
    for item in log.parsed_output:
        vlan_id = int(item.get("vlan_id"))
        vlan_name = item.get("name")

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
