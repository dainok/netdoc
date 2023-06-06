"""Ingestor for netmiko_cisco_nxos_show_vrf."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import vrf


def ingest(log):
    """Processing parsed output.

    VRF - Interface association is ingested in the "show ip interface" output.
    """
    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/cisco_nxos/show_vrf # pylint: disable=line-too-long
        vrf_name = item.get("name")

        # Get or create VRF
        vrf_o = None
        if vrf_name and vrf_name != "default":
            vrf_o = vrf.get(name=vrf_name)
            if not vrf_o:
                data = {
                    "name": vrf_name,
                }
                vrf_o = vrf.create(**data)

    # Update the log
    log.ingested = True
    log.save()
