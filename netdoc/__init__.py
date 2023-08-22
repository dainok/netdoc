"""Main class."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import os
import pkgutil
import shutil

from django.conf import settings

from extras.plugins import PluginConfig


PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netdoc", {})


class NetdocConfig(PluginConfig):
    """Configuration class."""

    name = "netdoc"
    verbose_name = "NetDoc"
    description = "Automatic Network Documentation plugin for NetBox"
    version = "0.0.1-dev1"
    author = "Andrea Dainese"
    author_email = "andrea@adainese.it"
    base_url = "netdoc"
    required_settings = ["NTC_TEMPLATES_DIR"]
    default_settings = {
        "MAX_INGESTED_LOGS": 50,
        "NTC_TEMPLATES_DIR": "/opt/ntc-templates/ntc_templates/templates",
        "NORNIR_LOG": f"{settings.BASE_DIR}/nornir.log",
        "NORNIR_TIMEOUT": 300,
        "RAISE_ON_CDP_FAIL": True,
        "RAISE_ON_LLDP_FAIL": True,
        "ROLE_MAP": {},
    }

    def ready(self):
        """Load signals."""
        from netdoc import (  # noqa: F401 pylint: disable=import-outside-toplevel,unused-import
            signals,
        )

        super().ready()


config = NetdocConfig  # pylint: disable=invalid-name

# Setting NTC_TEMPLATES_DIR
os.environ.setdefault("NET_TEXTFSM", PLUGIN_SETTINGS.get("NTC_TEMPLATES_DIR"))

# Copy scripts
package = pkgutil.get_loader("netdoc")
MODULE_PATH = os.path.dirname(package.path)
SCRIPTS_PATH = os.path.join(MODULE_PATH, "scripts")
for filename in os.listdir(SCRIPTS_PATH):
    src_file = os.path.join(SCRIPTS_PATH, filename)
    dst_file = os.path.join(settings.SCRIPTS_ROOT, filename)
    if (
        filename.startswith("__init__")
        or not filename.endswith(".py")
        or not os.path.isfile(src_file)
    ):
        # Not a script file
        continue
    # Copy file in Netbox root scripts path
    shutil.copy(src_file, dst_file)

# Copy reports
REPORTS_PATH = os.path.join(MODULE_PATH, "reports")
for filename in os.listdir(REPORTS_PATH):
    src_file = os.path.join(REPORTS_PATH, filename)
    dst_file = os.path.join(settings.REPORTS_ROOT, filename)
    if (
        filename.startswith("__init__")
        or not filename.endswith(".py")
        or not os.path.isfile(src_file)
    ):
        # Not a report file
        continue
    # Copy file in Netbox root reports path
    shutil.copy(src_file, dst_file)
