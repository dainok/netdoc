"""Script used to manually import Discoverables."""  # pylint: disable=invalid-name

__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from datetime import date, timedelta
import re
import netaddr

from django.conf import settings

from dcim.models import Site, DeviceRole, Interface, Device
from ipam.models import IPAddress
from extras.scripts import (
    Script,
    ChoiceVar,
    ObjectVar,
    MultiObjectVar,
    TextVar,
    BooleanVar,
    IntegerVar,
)

from netdoc.models import (
    DiscoveryModeChoices,
    Discoverable as Discoverable_m,
    Credential as Credential_m,
    DiscoveryLog as DiscoveryLog_m,
    ArpTableEntry as ArpTableEntry_m,
    MacAddressTableEntry as MacAddressTableEntry_m,
    DeviceImageChoices,
)
from netdoc.utils import (
    log_ingest,
    normalize_interface_label,
    normalize_hostname,
    spawn_script,
)
from netdoc.schemas import discoverable
from netdoc.tasks import discovery

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netdoc", {})
NORNIR_LOG = PLUGIN_SETTINGS.get("NORNIR_LOG")


class CreateDeviceRole(Script):
    """Script used to create DeviceRole used in Diagram.

    DeviceRole.slug is used to draw the icon in diagrams.
    """

    class Meta:
        """Script metadata."""

        name = "Create device roles"
        description = "Add device roles based on available PNG."
        commit_default = True

    def run(self, data, commit):
        """Start the script."""
        icons = DeviceImageChoices()
        for key, value in icons:
            try:
                DeviceRole.objects.get(slug=key)
                self.log_info(f"DeviceRole {key} found")
            except DeviceRole.DoesNotExist:  # pylint: disable=no-member
                self.log_warning(f"Created DeviceRole {key}")
                DeviceRole.objects.create(name=value, slug=key)


class AddDiscoverable(Script):
    """Script used to generate AddDiscoverable."""

    class Meta:
        """Script metadata."""

        name = "Add and discover"
        description = "Add comma separated IP addresses and discover them."
        commit_default = True

    # Credentials
    credential = ObjectVar(
        model=Credential_m,
        description="Credential used to discover.",
        required=True,
    )

    # Discovery mode
    mode = ChoiceVar(
        choices=DiscoveryModeChoices.CHOICES,
        description="Discovery mode",
        required=True,
    )

    # Site
    site = ObjectVar(
        model=Site,
        description="Site associated with discovered devices",
        required=True,
    )

    # IP addresses to be discovered
    ip_addresses = TextVar(
        description="IP addresses separated by comma or space",
        required=True,
    )

    def run(self, data, commit):
        """Start the script."""
        discoverable_ip_addresses = []

        if not commit:
            self.log_warning("Commit not set, using dry-run mode")

        credential_o = data.get("credential")
        mode = data.get("mode")
        site_o = data.get("site")
        ip_addresses = re.split(" |,|\n", data.get("ip_addresses"))

        # Parse IP addresses
        for ip_address in ip_addresses:
            ip_address = ip_address.strip()
            if not ip_address:
                # Skip empty string
                continue

            try:
                netaddr.IPAddress(ip_address)
            except netaddr.core.AddrFormatError:
                # Skip invalid IP address
                self.log_warning(f"Skipping invalid IP address {ip_address}")
                continue

            # Create or get Discoverable
            discoverable_o, created = discoverable.get_or_create(
                address=ip_address,
                site_id=site_o.pk,
                mode=mode,
                credential_id=credential_o.pk,
                discoverable=True,
            )
            if created:
                self.log_info(
                    f"Created new discoverable with IP address {discoverable_o.address}"
                )
            else:
                self.log_info(
                    f"Using existing discoverable with IP address {discoverable_o.address}"
                )

            discoverable_ip_addresses.append(discoverable_o.address)

        if not discoverable_ip_addresses:
            self.log_failure("No valid IP address to discover")
            return ""

        self.log_info(f"Starting discovery on {', '.join(discoverable_ip_addresses)}")
        output = discovery(discoverable_ip_addresses, script_handler=self)

        self.log_info("Discovery completed")

        return output


class Discover(Script):
    """Script used to start discovery."""

    class Meta:
        """Script metadata."""

        name = "Discover"
        description = "Start discovery on one, many or all discoverables."
        commit_default = True

    # Discoverable
    discoverables = MultiObjectVar(
        model=Discoverable_m,
        query_params={
            "discoverable": True
        },  # TODO: not working, discoverable=False are also showed (cosmetic).
        description="Devices to be discovered (leave empty to discover everything).",
        required=False,
    )

    # Ingested?
    undiscovered_only = BooleanVar(
        description="Undiscovered devices only (the above setting is ignored).",
        required=False,
        default=True,
    )

    def run(self, data, commit):
        """Start the script."""
        discoverable_ip_addresses = []
        discoverables = data.get("discoverables")

        # Filtering out discoverable=False is done at Nornir inventory level.

        if data.get("undiscovered_only"):
            # Get only undiscovered IP addresses
            discoverables = discoverable.get_list(last_discovered_at__isnull=True)
            for discoverable_o in discoverables:
                discoverable_ip_addresses.append(discoverable_o.address)

            self.log_info(
                f"Starting first discovery on {', '.join(discoverable_ip_addresses)}"
            )
            output = discovery(discoverable_ip_addresses, script_handler=self)
        elif discoverables:
            for discoverable_o in discoverables:
                discoverable_ip_addresses.append(discoverable_o.address)

            self.log_info(
                f"Starting discovery on {', '.join(discoverable_ip_addresses)}"
            )
            output = discovery(discoverable_ip_addresses, script_handler=self)
        else:
            self.log_info("Starting discovery on all IP addresses")
            output = discovery(None, script_handler=self)

        return output


class Ingest(Script):
    """Script used to start ingestion."""

    class Meta:
        """Script metadata."""

        name = "Ingest"
        description = (
            "Start data ingestion (automatically triggered after a discovery)."
        )
        commit_default = True

    # Discoverable
    discoverables = MultiObjectVar(
        model=Discoverable_m,
        description="Limit ingestion to selected discoverables.",
        required=False,
    )

    # Ingested?
    re_ingest = BooleanVar(
        description="Force re-ingestion.",
        required=False,
    )

    # Maximum logs to ingest
    max_ingested_logs = IntegerVar(
        description="Maximum logs to ingest before spawning another job",
        required=False,
    )

    def run(self, data, commit):
        """Start the script."""
        log_queryset = DiscoveryLog_m.objects.filter(parsed=True).order_by("order")
        remaining_logs = 0
        if not data.get("re_ingest"):
            # Filter out logs already ingested
            log_queryset = log_queryset.filter(ingested=False)
        if data.get("discoverables"):
            log_queryset = log_queryset.filter(
                discoverable__in=data.get("discoverables")
            )
        if data.get("max_ingested_logs"):
            max_ingested_logs = data.get("max_ingested_logs")
            self.log_info(f"Limiting ingesting to {max_ingested_logs} logs")
            remaining_logs = len(log_queryset) - max_ingested_logs
            log_queryset = log_queryset[:max_ingested_logs]

        if log_queryset:
            self.log_info(f"Ingesting {len(log_queryset)} logs")
        else:
            self.log_failure("No log to ingest")

        for log in log_queryset:
            if log.ingested:
                self.log_info(
                    f"Reingesting log {log.id} with command {log.command} "
                    + f"on device {log.discoverable}"
                )
            else:
                self.log_info(
                    f"Ingesting log {log.id} with command {log.command} on "
                    + f"device {log.discoverable}"
                )
            log_ingest(log)

        if remaining_logs > 0:
            # Need to span another job
            self.log_info(f"Spawning a new job to ingest {remaining_logs} logs")
            spawn_script("Ingest", post_data=data, user=self.request.user)


class Purge(Script):
    """Script used to delete old data."""

    class Meta:
        """Script metadata."""

        name = "Purge"
        description = "Delete old logs, ARP table entries, MAC Address table entries."
        commit_default = True

    # Minimum days to delete
    days = IntegerVar(
        description="Minimum age in days to delete",
        required=True,
        default=90,
    )

    def run(self, data, commit):
        """Start the script."""
        today = date.today()
        today_minus_x = today - timedelta(days=data.get("days"))

        discoverylogs_qs = DiscoveryLog_m.objects.filter(created__lt=today_minus_x)
        arpentries_qs = ArpTableEntry_m.objects.filter(last_updated__lt=today_minus_x)
        macaddressentries_qs = MacAddressTableEntry_m.objects.filter(
            last_updated__lt=today_minus_x
        )

        self.log_info(f"Deleting entries updated before f{today_minus_x}")
        self.log_info(f"Deleting {len(discoverylogs_qs)} discovery logs")
        if discoverylogs_qs:
            discoverylogs_qs.delete()
        self.log_info(f"Deleting {len(arpentries_qs)} ARP table entries")
        if arpentries_qs:
            arpentries_qs.delete()
        self.log_info(f"Deleting {len(macaddressentries_qs)} MAC address table entries")
        if macaddressentries_qs:
            macaddressentries_qs.delete()
        self.log_info("Purge completed")


class IPAMFromARP(Script):
    """Create IP Address on IPAM based on ARP table."""

    class Meta:
        """Script metadata."""

        name = "Update IPAM from ARP tables"
        description = (
            "Create IP Address on IPAM based on ARP table. Should be started after "
            + "VRFIpPrefixIntegrityCheck report."
        )
        commit_default = True

    def run(self, data, commit):
        """For each ARP, check if an IPAddress exist and create it if it doesn't.

        ARPTableEntry.Interface.IPAddress.VRF must be equal to Prefix.VRF.
        """
        for arptableentry_o in ArpTableEntry_m.objects.all():
            try:
                interface_vrf_o = arptableentry_o.interface.ip_addresses.first().vrf
            except AttributeError:
                self.log_failure(
                    f"IP address not found on interface {arptableentry_o.interface}, maybe "
                    + "some ingestion script has failed",
                )
                continue

            # IP address with prefixlen built from ARP table and associated interface
            address = str(arptableentry_o.ip_address.ip)
            prefixlen = (
                arptableentry_o.interface.ip_addresses.filter(
                    address__net_contains_or_equals=address
                )
                .first()
                .address.prefixlen
            )
            ip_address = f"{address}/{prefixlen}"

            # Query for the IP address in the IPAM
            ipaddresses_qs = IPAddress.objects.filter(
                vrf=interface_vrf_o, address=ip_address
            )
            if not ipaddresses_qs:
                IPAddress.objects.create(address=ip_address, vrf=interface_vrf_o)
                self.log_info(
                    f"IP address {ip_address} with VRF {interface_vrf_o} added in IPAM",
                )


class FixData(Script):
    """Fix Device names and Interface labels."""

    class Meta:
        """Script metadata."""

        name = "Fix Netbox data"
        description = (
            "Fix Netbox data to be used with NetDoc (Device names, Interface labels)."
        )
        commit_default = True

    def run(self, data, commit):
        """Test and fix Netbox data."""
        # Test Device name
        device_qs = Device.objects.all()
        for device_o in device_qs:
            name = device_o.name
            new_name = normalize_hostname(name)

            if name == new_name:
                self.log_info(f"{device_o} has name {new_name}")
            else:
                self.log_warning(f"Renaming device {device_o} to {new_name}")
                device_o.name = new_name
                device_o.save()

        # Test Interface name/label integrity
        interface_qs = Interface.objects.all()
        for interface_o in interface_qs:
            name = interface_o.name
            new_label = normalize_interface_label(name)

            if interface_o.label == new_label:
                self.log_info(f"{interface_o} has label {new_label}")
            else:
                self.log_warning(
                    f"Renaming label {interface_o.label} to {new_label} for interface {interface_o}"
                )
                interface_o.label = new_label
                interface_o.save()
