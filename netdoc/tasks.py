"""Tasks executed via Netbox scripts or manually."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import importlib
import os
import logging
import pprint
import tempfile

from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir import InitNornir
from nornir.core.filter import F

from django.conf import settings

from netdoc.nornir_inventory import AssetInventory
from netdoc.models import DiscoveryModeChoices
from netdoc import utils

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netdoc", {})


def discovery(addresses=None, script_handler=None, filters=None, filter_type=None):
    """Discovery all or a list of IP addresses."""
    if not addresses:
        addresses = []
    if not filters:
        filters = []
    ntc_template_dir = os.environ.get("NET_TEXTFSM")

    if not ntc_template_dir:
        raise ValueError("NET_TEXTFSM not set in configuration.py")
    if not os.path.exists(ntc_template_dir):
        raise ValueError(f"{ntc_template_dir} not found")

    # Configuring Nornir
    logger = logging.getLogger("nornir")
    logger.setLevel(logging.DEBUG)
    if script_handler:
        log_filename = os.path.join(
            tempfile.gettempdir(), f"nornir-{utils.get_random_string(6)}.log"
        )
    else:
        log_filename = PLUGIN_SETTINGS.get("NORNIR_LOG")
    file_h = logging.FileHandler(log_filename)
    file_h.setLevel(logging.DEBUG)
    logger.addHandler(file_h)

    # Load Nornir custom inventory
    InventoryPluginRegister.register("asset-inventory", AssetInventory)

    # Create Nornir inventory
    nrni = InitNornir(
        runner={
            "plugin": "threaded",
            "options": {
                "num_workers": 10,
            },
        },
        inventory={"plugin": "asset-inventory"},
        logging={"enabled": False},
    )

    if addresses:
        # Execute on selected hosts only
        # See https://theworldsgonemad.net/2021/nornir-inventory/
        pprint.pprint(addresses)
        nrni = nrni.filter(F(hostname__in=addresses))

    # Starting discovery job
    nornir_addresses = nrni.dict().get("inventory").get("hosts").keys()
    pprint.pprint(nornir_addresses)
    if script_handler:
        if not nornir_addresses:
            script_handler.log_failure("Nornir inventory is empty")
            return ""
        script_handler.log_info(
            f"Norninr inventory includes {', '.join(nornir_addresses)}"
        )

    if filters:
        script_handler.log_info(
            f"The following {filter_type} filter has been configured {', '.join(filters)}"
        )

    # Run discovery scripts
    for mode, description in DiscoveryModeChoices():
        # framework = mode.split("_").pop(0)
        platform = "_".join(mode.split("_")[1:])
        filtered_devices = nrni.filter(platform=platform)
        filtered_addresses = (
            filtered_devices.dict().get("inventory").get("hosts").keys()
        )
        if not filtered_addresses:
            if script_handler:
                script_handler.log_warning(f"No {description} device found")
            continue
        if script_handler:
            script_handler.log_info(f"Starting discovery of {description} devices")
            script_handler.log_info(
                f"Nornir inventory includes {', '.join(filtered_addresses)}"
            )
        # Call the discovery script
        try:
            module = importlib.import_module(f"netdoc.discoverers.{mode}")
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(f"Discovery script not found for {mode}") from exc
        module.discovery(filtered_devices, filters=filters, filter_type=filter_type)

    if script_handler:
        script_handler.log_info("Discovery completed")

    # Return log
    with open(log_filename, "r", encoding="utf-8") as fh_o:
        output = fh_o.read()
    if script_handler:
        # Delete log file
        os.remove(log_filename)
        # Spawan ingest script
        script_handler.log_info("Spawning ingest script")
        utils.spawn_script("Ingest")

    return output
