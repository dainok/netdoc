"""Ingestor for linux_ip_vrf_show."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import vrf


def ingest(log):
    """Processing parsed output."""
    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/linux/ip_vrf_show # pylint: disable=line-too-long
        vrf_name = item.get("vrf")

        vrf_o = vrf.get(name=vrf_name)
        if not vrf_o:
            data = {
                "name": vrf_name,
            }
            vrf_o = vrf.create(mandatory_rd=False, **data)

    # Update the log
    log.ingested = True
    log.save()
