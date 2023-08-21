"""Ingestor for netmiko_cisco_xr_show_vrf_all_detail."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import vrf
from netdoc import utils


def ingest(log):
    """Processing parsed output.

    VRF - Interface association is ingested in the "show ip interface" output.
    """
    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/cisco_nxos/show_vrf # pylint: disable=line-too-long
        vrf_name = utils.normalize_vrf_name(item.get("vrf"))
        vrf_rd = utils.normalize_rd(item.get("rd"))

        # Get or create VRF
        if vrf_name:
            vrf_o = vrf.get_or_create(name=vrf_name)[0]
            vrf_o = vrf.update(vrf_o, mandatory_rd=False, rd=vrf_rd)

    # Update the log
    log.ingested = True
    log.save()
