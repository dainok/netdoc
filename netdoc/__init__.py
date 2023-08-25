"""Main class."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import sys
import os
import pkgutil

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
        "MAX_INGESTED_LOGS": 25,
        "NTC_TEMPLATES_DIR": "/opt/ntc-templates/ntc_templates/templates",
        "NORNIR_LOG": f"{settings.BASE_DIR}/nornir.log",
        "NORNIR_TIMEOUT": 300,
        "RAISE_ON_CDP_FAIL": True,
        "RAISE_ON_LLDP_FAIL": True,
        "ROLE_MAP": {},
    }

    def ready(self):
        """Load signals and create reports/scripts."""
        if "migrate" not in sys.argv:
            from netdoc import (  # noqa: F401 pylint: disable=import-outside-toplevel,unused-import
                signals,
            )
            from core.models import (  # noqa: F401 pylint: disable=import-outside-toplevel
                DataSource,
                DataFile,
            )
            from extras.models import (  # noqa: F401 pylint: disable=import-outside-toplevel
                ScriptModule,
                ReportModule,
            )

            # Create/update data sources for NetDoc scripts on every restart
            package = pkgutil.get_loader("netdoc")
            module_path = os.path.dirname(package.path)
            jobs_path = os.path.join(module_path, "jobs")
            try:
                jobs_ds_o = DataSource.objects.get(name="netdoc_jobs")
                jobs_ds_o.url = jobs_path
                jobs_ds_o.save()
            except DataSource.DoesNotExist:  # pylint: disable=no-member
                jobs_ds_o = DataSource.objects.create(
                    name="netdoc_jobs", type="local", source_url=jobs_path
                )

            # Create/update NetDoc scripts on every restart
            script_filename = "netdoc_scripts.py"
            script_file_o = DataFile.objects.get(path=script_filename)
            try:
                script_o = ScriptModule.objects.get(data_file=script_file_o)
                script_o.auto_sync_enabled = True
                script_o.save()
            except ScriptModule.DoesNotExist:  # pylint: disable=no-member
                script_o = ScriptModule.objects.create(
                    data_file=script_file_o, auto_sync_enabled=True
                )
                script_o.clean()
                script_o.save()

            # Create/update NetDoc reports on every restart
            report_filename = "netdoc_reports.py"
            report_file_o = DataFile.objects.get(path=report_filename)
            try:
                report_o = ReportModule.objects.get(data_file=report_file_o)
                report_o.auto_sync_enabled = True
                report_o.save()
            except ReportModule.DoesNotExist:  # pylint: disable=no-member
                report_o = ReportModule.objects.create(
                    data_file=report_file_o, auto_sync_enabled=True
                )
                report_o.clean()
                report_o.save()

        super().ready()


config = NetdocConfig  # pylint: disable=invalid-name

# Setting NTC_TEMPLATES_DIR
os.environ.setdefault("NET_TEXTFSM", PLUGIN_SETTINGS.get("NTC_TEMPLATES_DIR"))
