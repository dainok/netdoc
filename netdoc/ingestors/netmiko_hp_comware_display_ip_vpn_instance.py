"""Ingestor for netmiko_hp_comware_display_ip_vpn_instance."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import vrf


def ingest(log):
    """Processing parsed output.

    VRF - Interface association is ingested in the output of:
    "display ip vpn-instance instance-name <vrf>"
    """
    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/hp_comware/display_ip_vpn-instance # pylint: disable=line-too-long
        vrf_name = item.get("name")
        vrf_rd = item.get("default_rd") if item.get("default_rd") else None

        data = {
            "name": vrf_name,
            "rd": vrf_rd,
        }
        vrf_o = vrf.get(name=vrf_name)
        if vrf_o:
            vrf_o = vrf.update(vrf_o, mandatory_rd=False, **data)
        else:
            vrf_o = vrf.create(mandatory_rd=False, **data)

    # Update the log
    log.ingested = True
    log.save()
