"""Ingestor for linux_ip_vrf_show."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.schemas import vrf
from netdoc import utils


def ingest(log):
    """Processing parsed output."""
    for item in log.parsed_output:
        # See https://github.com/networktocode/ntc-templates/tree/master/tests/linux/ip_vrf_show # pylint: disable=line-too-long
        vrf_name = utils.normalize_vrf_name(item.get("vrf"))

        # Get or create VRF
        if vrf_name:
            vrf.get_or_create(name=vrf_name)

    # Update the log
    log.ingested = True
    log.save()
