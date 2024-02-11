"""Ingestor for netmiko_allied_telesis_show_vlan_all."""
__remodeler__ = "tatumi0726"
__contact__ = "tatumi0726@gmail.com"
__copyright__ = "Copyright 2023, tatumi0726"
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
