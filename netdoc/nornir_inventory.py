"""Custom Inventory for Nornir."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from nornir.core.inventory import (
    Inventory,
    Host,
    Hosts,
    Group,
    Groups,
    ParentGroups,
    Defaults,
    ConnectionOptions,
)

from django.conf import settings

from netdoc import models

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netdoc", {})


class AssetInventory:
    """Build Nornir AssetInventory.

    AssetInventory is an inventory plugin for Nornir that loads data from
    Discoverable table. Can be registered and used with:

    from nornir.core.plugins.inventory import InventoryPluginRegister
    from netdoc.nornir_inventory import AssetInventory
    from nornir import InitNornir

    InventoryPluginRegister.register("asset-inventory", AssetInventory)
    nr = InitNornir(
        runner={
            "plugin": "threaded",
            "options": {
                "num_workers": 100,
            },
        },
        inventory={
            "plugin": "asset-inventory",
        },
        logging={"enabled": False},
    )
    """

    def load(self) -> Inventory:
        """Load items from remote API."""
        defaults = Defaults()
        hosts = Hosts()
        groups = Groups()

        discoverables = models.Discoverable.objects.filter(discoverable=True)

        # Add "all" group
        groups["all"] = Group("all")

        # Load discoverable hosts
        for discoverable in discoverables:
            credential = discoverable.credential
            # Add hosts discoverable via Netmiko
            device_type = "_".join(discoverable.mode.split("_")[1:])
            data = {
                "site_id": discoverable.site.pk,
                "site": discoverable.site.slug,
            }

            host_key = discoverable.address
            host_groups = [device_type, f'site-{data["site"]}']

            # Create additional options
            extras = {}
            if credential.enable_password:
                extras["secret"] = credential.enable_password
            connection_options = {"netmiko": ConnectionOptions(extras=extras)}

            hosts[host_key] = Host(
                name=host_key,
                hostname=discoverable.address,
                username=credential.username,
                password=credential.password,
                port=22,
                platform=device_type,
                data=data,
                groups=ParentGroups(),
                connection_options=connection_options,
            )  # name is the key used in AggregatedResults, the form is: tenant:id:ip_address

            # Add groups
            for host_group in host_groups:
                if host_group not in dict(groups):
                    groups[host_group] = Group(host_group)
                hosts[host_key].groups.append(Group(host_group))

        return Inventory(hosts=hosts, groups=groups, defaults=defaults)
