"""
Clean previous data, load lab-specific content, and test.

To make the process faster, the database is created once and resued:
    - /opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py test netdoc --verbosity=2 --keepdb
"""

from os import walk, path
import re
import json
import yaml
from yaml.loader import SafeLoader

from django.test import TestCase
from django.db.models import Q

from dcim.models import (
    Device,
    DeviceRole,
    DeviceType,
    Manufacturer,
    Cable,
    CableTermination,
    Interface,
    CablePath,
    Site,
)
from ipam.models import IPAddress, Prefix, VRF, VLAN
from virtualization.models import VirtualMachine, VMInterface, ClusterType, Cluster

from netdoc.models import (
    ArpTableEntry,
    MacAddressTableEntry,
    RouteTableEntry,
    Discoverable,
    Credential,
    DiscoveryLog,
)
from netdoc.schemas import (
    credential as credential_api,
    discoverable as discoverable_api,
    discoverylog as discoverylog_api,
)
from netdoc.utils import log_ingest

TEST_DIRECTORY = path.dirname(path.realpath(__file__))


def test_devices(test_o, expected_results):
    """Test Device given an expected_results dict."""
    # Test total Device objects
    device_qs = Device.objects.all()
    test_o.assertEquals(len(device_qs), len(expected_results), "number of results")

    # Test each item
    for expected_result in expected_results:
        device_o = Device.objects.get(name=expected_result.get("name"))
        test_o.assertEquals(
            device_o.device_type.model, expected_result.get("model"), "model"
        )
        test_o.assertEquals(
            device_o.device_type.manufacturer.name,
            expected_result.get("manufacturer"),
            "manufacturer",
        )
        test_o.assertEquals(device_o.serial, expected_result.get("serial"), "serial")

        if device_o.site:
            test_o.assertEquals(device_o.site.name, expected_result.get("site"), "site")
        else:
            test_o.assertIs(expected_result.get("site"), None, "site")

        if device_o.primary_ip:
            test_o.assertEquals(
                str(device_o.primary_ip.address),
                expected_result.get("address"),
                "address",
            )
        else:
            test_o.assertIs(expected_result.get("address"), None, "address")


def test_discoverables(test_o, expected_results):
    """Test Discoverable given an expected_results dict."""
    # Test total Discoverable objects
    discoverable_qs = Discoverable.objects.all()
    test_o.assertEquals(
        len(discoverable_qs), len(expected_results), "number of results"
    )

    # Test each item
    for expected_result in expected_results:
        discoverable_o = Discoverable.objects.get(
            address=expected_result.get("address")
        )
        test_o.assertEquals(discoverable_o.mode, expected_result.get("mode"), "mode")

        if discoverable_o.device:
            test_o.assertEquals(
                discoverable_o.device.name, expected_result.get("device"), "device"
            )
        else:
            test_o.assertIs(expected_result.get("device"), None, "device")

        if discoverable_o.vm:
            test_o.assertEquals(discoverable_o.vm.name, expected_result.get("vm"), "vm")
        else:
            test_o.assertIs(expected_result.get("vm"), None, "vm")

        if discoverable_o.site:
            test_o.assertEquals(
                discoverable_o.site.name, expected_result.get("site"), "site"
            )
        else:
            test_o.assertIs(expected_result.get("site"), None, "site")

        if discoverable_o.credential:
            test_o.assertEquals(
                discoverable_o.credential.name,
                expected_result.get("credential"),
                "credential",
            )
        else:
            test_o.assertIs(expected_result.get("credential"), None, "credential")


def test_interfaces(test_o, expected_results):
    """Test Interface given an expected_results dict."""
    # Test total Interface objects
    ipaddress_qs = Interface.objects.all()
    test_o.assertEquals(
        len(ipaddress_qs),
        len(
            [
                interface_value
                for device_name in list(expected_results.values())
                for interface_value in device_name
            ]
        ),
        "number of results",
    )

    # Test each device
    for device_name, interface_list in expected_results.items():
        # Test each interface
        for interface_value in interface_list:
            interface_o = Interface.objects.get(
                label=interface_value.get("label"), device__name=device_name
            )
            test_o.assertEquals(interface_o.type, interface_value.get("type"), "type")
            test_o.assertEquals(
                interface_o.speed, interface_value.get("speed"), "speed"
            )
            test_o.assertEquals(
                interface_o.duplex, interface_value.get("duplex"), "duplex"
            )
            test_o.assertEquals(interface_o.mtu, interface_value.get("mtu"), "mtu")
            test_o.assertEquals(
                interface_o.enabled, interface_value.get("enabled"), "enabled"
            )
            test_o.assertEquals(
                interface_o.description,
                interface_value.get("description"),
                "description",
            )
            test_o.assertEquals(interface_o.mode, interface_value.get("mode"), "mode")

            if interface_value.get("name"):
                # Check Interface.name only if is not None on interfaces.yml
                test_o.assertEquals(
                    interface_o.name, interface_value.get("name"), "name"
                )

            if interface_o.mac_address:
                test_o.assertEquals(
                    str(interface_o.mac_address),
                    interface_value.get("mac_address", "mac_address"),
                )
            else:
                test_o.assertIs(interface_value.get("mac_address"), None, "mac_address")

            if interface_o.vrf:
                test_o.assertEquals(
                    interface_o.vrf.name, interface_value.get("vrf"), "vrf"
                )
            else:
                test_o.assertIs(interface_value.get("vrf"), None, "vrf")

            if interface_o.parent:
                test_o.assertEquals(
                    interface_o.parent.label, interface_value.get("parent", "parent")
                )
            else:
                test_o.assertIs(interface_value.get("parent"), None, "parent")

            if interface_o.lag:
                test_o.assertEquals(
                    interface_o.lag.label, interface_value.get("lag"), "lag"
                )
            else:
                test_o.assertIs(interface_value.get("lag"), None, "lag")

            if interface_o.connected_endpoints:
                test_o.assertEquals(
                    interface_o.connected_endpoints[0].device.name,
                    interface_value.get("connected_device"),
                    "connected_device",
                )
                test_o.assertEquals(
                    interface_o.connected_endpoints[0].label,
                    interface_value.get("connected_interface_label"),
                    "connected_interface_label",
                )
            else:
                test_o.assertIs(
                    interface_value.get("connected_device"), None, "connected_device"
                )
                test_o.assertIs(
                    interface_value.get("connected_interface_label"),
                    None,
                    "connected_interface_label",
                )

            if interface_o.untagged_vlan:
                test_o.assertEquals(
                    interface_o.untagged_vlan.vid,
                    interface_value.get("untagged_vlan"),
                    "untagged_vlan",
                )
            else:
                test_o.assertIs(
                    interface_value.get("untagged_vlan"), None, "untagged_vlan"
                )

            test_o.assertEquals(
                len(interface_o.tagged_vlans.all()),
                len(interface_value.get("tagged_vlans")),
                "tagged_vlans",
            )
            for vlan_o in interface_o.tagged_vlans.all():
                test_o.assertIn(
                    vlan_o.vid, interface_value.get("tagged_vlans"), "tagged_vlans"
                )

            test_o.assertEquals(
                len(interface_o.ip_addresses.all()),
                len(interface_value.get("ip_addresses")),
                "ip_addresses",
            )
            for ipaddress_o in interface_o.ip_addresses.all():
                test_o.assertIn(
                    str(ipaddress_o.address),
                    interface_value.get("ip_addresses"),
                    "ip_addresses",
                )


def test_ipaddresses(test_o, expected_results):
    """Test IPAddress given an expected_results dict."""
    # Test total IPAddress objects
    ipaddress_qs = IPAddress.objects.all()
    test_o.assertEquals(len(ipaddress_qs), len(expected_results), "number of results")

    # Test each item
    for expected_result in expected_results:
        if expected_result.get("vrf"):
            IPAddress.objects.get(
                address=expected_result.get("address"),
                vrf__name=expected_result.get("vrf"),
            )
        else:
            IPAddress.objects.get(address=expected_result.get("address"))


def test_prefixes(test_o, expected_results):
    """Test Prefix given an expected_results dict."""
    # Test total Prefix objects
    prefix_qs = Prefix.objects.all()
    test_o.assertEquals(len(prefix_qs), len(expected_results), "number of results")

    # Test each item
    for expected_result in expected_results:
        if expected_result.get("vrf"):
            prefix_o = Prefix.objects.get(
                prefix=expected_result.get("prefix"),
                vrf__name=expected_result.get("vrf"),
            )
        else:
            prefix_o = Prefix.objects.get(prefix=expected_result.get("prefix"))

        if prefix_o.vrf:
            test_o.assertEquals(prefix_o.vrf.name, expected_result.get("vrf"), "vrf")
        else:
            test_o.assertIs(expected_result.get("vrf"), None, "vrf")

        if prefix_o.site:
            test_o.assertEquals(prefix_o.site.name, expected_result.get("site"), "site")
        else:
            test_o.assertIs(expected_result.get("site"), None, "site")


def test_vlans(test_o, expected_results):
    """Test VLAN given an expected_results dict."""
    # Test total VLAN objects
    vlan_qs = VLAN.objects.all()
    test_o.assertEquals(len(vlan_qs), len(expected_results), "number of results")

    # Test each item
    for expected_result in expected_results:
        vlan_o = VLAN.objects.get(vid=int(expected_result.get("vid")))
        test_o.assertEquals(vlan_o.name, expected_result.get("name"), "name")


def test_vrfs(test_o, expected_results):
    """Test VRF given an expected_results dict."""
    # Test total VRF objects
    vrf_qs = VRF.objects.all()
    test_o.assertEquals(len(vrf_qs), len(expected_results))

    # Test each item
    for expected_result in expected_results:
        vrf_o = VRF.objects.get(name=expected_result.get("name"))
        test_o.assertEquals(vrf_o.rd, expected_result.get("rd"), "rd")


def test_macaddresses(test_o, expected_results):
    """Test VRF given an expected_results dict."""
    # Test total MacAddressTableEntry objects
    macaddress_qs = MacAddressTableEntry.objects.all()
    test_o.assertEquals(len(macaddress_qs), len(expected_results), "number of results")

    # Test each item
    for expected_result in expected_results:
        macaddress_o = MacAddressTableEntry.objects.get(
            interface__device__name=expected_result.get("device"),
            interface__label=expected_result.get("interface"),
            mac_address=expected_result.get("mac_address"),
            vvid=expected_result.get("vlan"),
        )
        test_o.assertEquals(macaddress_o.vendor, expected_result.get("vendor"))


def test_arps(test_o, expected_results):
    """Test ArpTableEntry given an expected_results dict."""
    # Test total ArpTableEntry objects
    arp_qs = ArpTableEntry.objects.all()
    test_o.assertEquals(len(arp_qs), len(expected_results), "number of results")

    # Test each item
    for expected_result in expected_results:
        if expected_result.get("interface"):
            arp_o = ArpTableEntry.objects.get(
                interface__device__name=expected_result.get("device"),
                interface__label=expected_result.get("interface"),
                mac_address=expected_result.get("mac_address"),
                ip_address=expected_result.get("ip_address") + "/32",
            )
        else:
            arp_o = ArpTableEntry.objects.get(
                virtual_interface__virtual_machine__name=expected_result.get("device"),
                virtual_interface__name=expected_result.get("virtual_interface"),
                mac_address=expected_result.get("mac_address"),
                ip_address=expected_result.get("ip_address") + "/32",
            )
        test_o.assertEquals(arp_o.vendor, expected_result.get("vendor"), "vendor")


def test_routes(test_o, expected_results):
    """Test RouteTableEntry given an expected_results dict."""
    # Test total RouteTableEntry objects
    route_qs = RouteTableEntry.objects.all()
    test_o.assertEquals(len(route_qs), len(expected_results), "number of results")

    # Test each item
    for expected_result in expected_results:
        if expected_result.get("nexthop_virtual_if"):
            route_o = RouteTableEntry.objects.get(
                vm__name=expected_result.get("device"),
                destination=expected_result.get("destination"),
                distance=expected_result.get("distance"),
                metric=expected_result.get("metric"),
                protocol=expected_result.get("protocol"),
                vrf__name=expected_result.get("vrf"),
                nexthop_ip=expected_result.get("nexthop_ip"),
                nexthop_virtual_if__name=expected_result.get("nexthop_virtual_if"),
            )
        elif expected_result.get("nexthop_if"):
            route_o = RouteTableEntry.objects.get(
                device__name=expected_result.get("device"),
                destination=expected_result.get("destination"),
                distance=expected_result.get("distance"),
                metric=expected_result.get("metric"),
                protocol=expected_result.get("protocol"),
                vrf__name=expected_result.get("vrf"),
                nexthop_ip=expected_result.get("nexthop_ip"),
                nexthop_if__label=expected_result.get("nexthop_if"),
            )
        else:
            route_o = RouteTableEntry.objects.filter(
                Q(device__name=expected_result.get("device"))
                | Q(vm__name=expected_result.get("device"))
            ).get(
                device__name=expected_result.get("device"),
                destination=expected_result.get("destination"),
                distance=expected_result.get("distance"),
                metric=expected_result.get("metric"),
                protocol=expected_result.get("protocol"),
                vrf__name=expected_result.get("vrf"),
                nexthop_ip=expected_result.get("nexthop_ip"),
                nexthop_if=None,
            )
        if route_o.nexthop_ip:
            test_o.assertEquals(
                str(route_o.nexthop_ip.ip),
                expected_result.get("nexthop_ip", "nexthop_ip"),
            )
        else:
            test_o.assertIs(expected_result.get("nexthop_ip"), None, "nexthop_ip")
        if route_o.nexthop_if:
            test_o.assertEquals(
                route_o.nexthop_if.label,
                expected_result.get("nexthop_if"),
                "nexthop_if",
            )
        else:
            test_o.assertIs(expected_result.get("nexthop_if"), None, "nexthop_if")


def test_virtual_machines(test_o, expected_results):
    """Test Virtual Machine given an expected_results dict."""
    # Test total Virtual Machine objects
    vm_qs = VirtualMachine.objects.all()
    test_o.assertEquals(len(vm_qs), len(expected_results), "number of results")

    # Test each item
    for expected_result in expected_results:
        vm_o = VirtualMachine.objects.get(name=expected_result.get("name"))
        test_o.assertEquals(vm_o.status, expected_result.get("status"), "status")
        if vm_o.vcpus:
            test_o.assertEquals(vm_o.vcpus, int(expected_result.get("vcpus")), "vcpus")
        else:
            test_o.assertIs(expected_result.get("vcpus"), None, "vcpus")
        if vm_o.memory:
            test_o.assertEquals(vm_o.memory, expected_result.get("memory"), "memory")
        else:
            test_o.assertIs(expected_result.get("memory"), None, "memory")
        if vm_o.disk:
            test_o.assertEquals(vm_o.disk, expected_result.get("disk"), "disk")
        else:
            test_o.assertIs(expected_result.get("disk"), None, "disk")

        if vm_o.site:
            test_o.assertEquals(vm_o.site.name, expected_result.get("site"), "site")
        else:
            test_o.assertIs(expected_result.get("site"), None, "site")

        if vm_o.cluster:
            test_o.assertEquals(
                vm_o.cluster.name, expected_result.get("cluster"), "cluster"
            )
        else:
            test_o.assertIs(expected_result.get("cluster"), None, "cluster")

        if vm_o.device:
            test_o.assertEquals(
                vm_o.device.name, expected_result.get("device"), "device"
            )
        else:
            test_o.assertIs(expected_result.get("device"), None, "device")

        if vm_o.primary_ip:
            test_o.assertEquals(
                str(vm_o.primary_ip.address),
                expected_result.get("address"),
                "address",
            )
        else:
            test_o.assertIs(expected_result.get("address"), None, "address")


def test_virtual_machine_interfaces(test_o, expected_results):
    """Test Interface given an expected_results dict."""
    # Test total Virtual Machine Interface objects
    ipaddress_qs = VMInterface.objects.all()
    test_o.assertEquals(
        len(ipaddress_qs),
        len(
            [
                interface_value
                for device_name in list(expected_results.values())
                for interface_value in device_name
            ]
        ),
        "number of results",
    )

    # Test each virtual interface
    for device_name, interface_list in expected_results.items():
        # Test each interface
        for interface_value in interface_list:
            interface_o = VMInterface.objects.get(
                name=interface_value.get("name"), virtual_machine__name=device_name
            )
            test_o.assertEquals(
                interface_o.enabled, interface_value.get("enabled"), "enabled"
            )
            test_o.assertEquals(interface_o.mtu, interface_value.get("mtu"), "mtu")

            if interface_o.mac_address:
                test_o.assertEquals(
                    str(interface_o.mac_address),
                    interface_value.get("mac_address"),
                    "mac_address",
                )
            else:
                test_o.assertIs(interface_value.get("mac_address"), None, "mac_address")

            test_o.assertEquals(
                interface_o.description,
                interface_value.get("description"),
                "description",
            )
            test_o.assertEquals(interface_o.mode, interface_value.get("mode"), "mode")

            if interface_o.parent:
                test_o.assertEquals(
                    interface_o.parent.name, interface_value.get("parent", "parent")
                )
            else:
                test_o.assertIs(interface_value.get("parent"), None, "parent")

            if interface_o.vrf:
                test_o.assertEquals(
                    interface_o.vrf.name, interface_value.get("vrf"), "vrf"
                )
            else:
                test_o.assertIs(interface_value.get("vrf"), None, "vrf")

            if interface_o.untagged_vlan:
                test_o.assertEquals(
                    interface_o.untagged_vlan.vid,
                    interface_value.get("untagged_vlan"),
                    "untagged_vlan",
                )
            else:
                test_o.assertIs(
                    interface_value.get("untagged_vlan"), None, "untagged_vlan"
                )

            test_o.assertEquals(
                len(interface_o.tagged_vlans.all()),
                len(interface_value.get("tagged_vlans")),
                "tagged_vlans",
            )
            for vlan_o in interface_o.tagged_vlans.all():
                test_o.assertIn(
                    vlan_o.vid, interface_value.get("tagged_vlans"), "tagged_vlans"
                )

            test_o.assertEquals(
                len(interface_o.ip_addresses.all()),
                len(interface_value.get("ip_addresses")),
                "ip_addresses",
            )
            for ipaddress_o in interface_o.ip_addresses.all():
                test_o.assertIn(
                    str(ipaddress_o.address),
                    interface_value.get("ip_addresses"),
                    "ip_addresses",
                )


def load_scenario(lab_path):
    """Load DiscoveryLog files and return the list of expected result files."""
    expected_result_files = []

    # Purge all data
    print("Deleting old data... ", end="")
    VMInterface.objects.all().delete()
    VirtualMachine.objects.all().delete()
    Cluster.objects.all().delete()
    ClusterType.objects.all().delete()
    Cable.objects.all().delete()
    CableTermination.objects.all().delete()
    CablePath.objects.all().delete()  # pylint: disable=no-member
    Device.objects.all().delete()
    DeviceRole.objects.all().delete()
    DeviceType.objects.all().delete()
    Manufacturer.objects.all().delete()
    Prefix.objects.all().delete()
    IPAddress.objects.all().delete()
    Interface.objects.all().delete()
    ArpTableEntry.objects.all().delete()
    MacAddressTableEntry.objects.all().delete()
    RouteTableEntry.objects.all().delete()
    VRF.objects.all().delete()
    VLAN.objects.all().delete()
    DiscoveryLog.objects.all().delete()
    Discoverable.objects.all().delete()
    Credential.objects.all().delete()
    Site.objects.all().delete()
    print("done")

    # Load scenario
    print(f"Loading scenario {lab_path}... ", end="")
    (
        credential_o,
        created,  # pylint: disable=unused-variable
    ) = credential_api.get_or_create(name="test-credential")
    site_o = Site.objects.create(name="test-site")

    for dirpath, dirnames, filenames in walk(  # pylint: disable=unused-variable
        lab_path
    ):
        for filename in filenames:
            if filename.endswith(".yml"):
                # Save expected result files
                expected_result_files.append(f"{dirpath}/{filename}")
            if filename.endswith(".json"):
                filepath_medata = f"{dirpath}/{filename}"
                filepath_raw_output = filepath_medata.replace(".json", ".raw")
                address = filename.split("-")[0]
                with open(filepath_medata, "r", encoding="utf-8") as log_fh:
                    # Load metadata
                    discoverablelog_json = json.load(log_fh)
                    discoverablelog_json["command"] = discoverablelog_json["details"][
                        "command"
                    ]
                    discoverablelog_json["order"] = discoverablelog_json["details"][
                        "order"
                    ]
                    discoverablelog_json["template"] = discoverablelog_json["details"][
                        "template"
                    ]
                with open(filepath_raw_output, "r", encoding="utf-8") as raw_fh:
                    # Load raw output
                    raw_output = raw_fh.read()

                # Get or create discoverable
                discoverable_o, created = discoverable_api.get_or_create(
                    address=address,
                    discoverable=False,
                    credential_id=credential_o.pk,
                    mode=discoverablelog_json.get("discoverable__mode"),
                    site_id=site_o.pk,
                )

                # Clear metadata and add raw output
                discoverablelog_json["raw_output"] = raw_output
                del discoverablelog_json["discoverable__mode"]

                # Create discoverylog
                discoverylog_api.create(
                    discoverable_id=discoverable_o.pk, **discoverablelog_json
                )
    print("done")

    # Ingest
    print("Ingesting... ", end="")
    logs_qs = DiscoveryLog.objects.filter(parsed=True, ingested=False).order_by("order")
    for log_o in logs_qs:
        log_ingest(log_o)
        log_o.ingested = True
        log_o.save()
    print("done")

    return expected_result_files


class QuestionModelTests(TestCase):
    """Automated test for Netdoc."""

    def test_scenario(self):
        """Run tests on each scenario."""
        for dirpath, dirnames, filenames in walk(  # pylint: disable=unused-variable
            TEST_DIRECTORY
        ):
            if re.match(r".*/lab\d+$", dirpath):
                # Found a test scenario (lab)
                # Load output files (DiscoveryLog)
                expected_result_files = load_scenario(dirpath)

                # Run test
                for expected_result_file in expected_result_files:
                    test_case = (
                        "test_" + expected_result_file.split("/")[-1].split(".")[0]
                    )
                    print(
                        f"Running {test_case} with file {expected_result_file}... ",
                        end="",
                    )
                    with open(expected_result_file, encoding="utf-8") as metadata_fh:
                        expected_results = yaml.load(metadata_fh, Loader=SafeLoader)
                    test_function = globals()[test_case]
                    test_function(self, expected_results)
                    print("done")
