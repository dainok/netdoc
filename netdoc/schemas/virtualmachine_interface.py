"""Schema validation for Interface."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from ipam.models import VLAN as VLAN_model, VRF as VRF_model
from virtualization.models.virtualmachines import VMInterface as VMInterface_model
from virtualization.models.virtualmachines import VirtualMachine as VirtualMachine_model
from dcim.choices import InterfaceModeChoices


from netdoc import utils
from netdoc.schemas import vlan, prefix, ipaddress


def get_schema():
    """Return the JSON schema to validate Device data."""
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
            },
            "virtual_machine_id": {
                "type": "integer",
                "enum": list(
                    VirtualMachine_model.objects.all().values_list("id", flat=True)
                ),
            },
            "vrf_id": {
                "type": "integer",
                "enum": list(VRF_model.objects.all().values_list("id", flat=True)),
            },
            "mac_address": {
                "type": "string",
            },
            "mtu": {
                "type": "integer",
            },
            "enabled": {
                "type": "boolean",
            },
            "parent_id": {
                "type": "integer",
                "enum": list(
                    VMInterface_model.objects.all().values_list("id", flat=True)
                ),
            },
            "bridge_id": {
                "type": "integer",
                "enum": list(
                    VMInterface_model.objects.all().values_list("id", flat=True)
                ),
            },
            "mode": {
                "type": "string",
                "enum": [key for key, value in InterfaceModeChoices()],
            },
            "untagged_vlan_id": {
                "type": "integer",
                "enum": list(VLAN_model.objects.all().values_list("vid", flat=True)),
            },
            "tagged_vlan_ids": {
                "type": "array",
                "item": {
                    "type": "integer",
                    "enum": list(
                        VLAN_model.objects.all().values_list("vid", flat=True)
                    ),
                },
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new Device objects."""
    schema = get_schema()
    schema["required"] = [
        "name",
        "type",
        "device_id",
    ]
    return schema


def create(**kwargs):  # pylint: disable=redefined-builtin
    """Create an Interface."""
    # The following are updated in update_mode
    if "mode" in kwargs:
        del kwargs["mode"]
    if "untagged_vlan_id" in kwargs:
        del kwargs["untagged_vlan_id"]
    if "tagged_vlan_ids" in kwargs:
        del kwargs["tagged_vlan_ids"]

    data = {
        **kwargs,
    }

    data = utils.delete_empty_keys(data)
    obj = utils.object_create(VMInterface_model, **data)
    return obj


def get(virtual_machine_id, name):
    """Return an Interface."""
    obj = utils.object_get_or_none(
        VMInterface_model, virtual_machine__id=virtual_machine_id, name=name
    )
    return obj


def get_list(**kwargs):
    """Get a list of Interface objects."""
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(VMInterface_model, **kwargs)
    return result


def update(obj, **kwargs):
    """Update an Interface."""
    update_always = [
        "name",
        "description",
        "vrf_id",
        "mac_address",
        "mtu",
        "enabled",
        "parent_id",
        "bridge_id",
    ]

    data = {
        **kwargs,
    }

    data = utils.delete_empty_keys(data)
    validate(data, get_schema(), format_checker=FormatChecker())
    kwargs_always = utils.filter_keys(data, update_always)
    obj = utils.object_update(obj, **kwargs_always)
    return obj


def update_mode(obj, mode=None, untagged_vlan=None, tagged_vlans=None):
    """Update an Interface mode.

    VLANs must exist.
    """
    if not tagged_vlans:
        tagged_vlans = []

    if mode == "tagged" and tagged_vlans and len(tagged_vlans) >= 4093:
        # Trunk with all VLANs (override mode)
        # In some switch the trunk is excluding native VLAN, so total is 4093.
        obj.mode = "tagged-all"
        obj.save()
    elif mode == "tagged":
        # Trunk with some VLANs
        # Query once to speed up the process
        current_tagged_vlan_list = list(
            obj.tagged_vlans.all().order_by("vid").values_list("vid", flat=True)
        )
        existent_vlan_qs = VLAN_model.objects.all()
        existent_vlan_list = list(
            existent_vlan_qs.values_list("vid", flat=True).order_by("vid").distinct()
        )
        vlans_to_be_created = []
        vlans_to_be_added = []
        vlans_to_be_removed = []

        # Find VLANs to be added
        for vid in tagged_vlans:
            if vid not in current_tagged_vlan_list:
                vlans_to_be_added.append(vid)

        # Find VLANs to be removed
        for vid in current_tagged_vlan_list:
            if vid not in tagged_vlans:
                vlans_to_be_removed.append(vid)

        # Find missing VLANs
        for tagged_vlan in tagged_vlans:
            if tagged_vlan not in existent_vlan_list:
                # VLAN needs to be created and added to interface (tagged)
                vlans_to_be_created.append(
                    VLAN_model(
                        vid=tagged_vlan, name=f"VLAN{tagged_vlan:04d}", status="active"
                    )
                )

        # Bulk create missing VLANs
        VLAN_model.objects.bulk_create(vlans_to_be_created)

        if vlans_to_be_added:
            # Add missing VLANs
            vlan_qs = existent_vlan_qs.filter(vid__in=vlans_to_be_added)
            obj.tagged_vlans.add(*vlan_qs)

        if vlans_to_be_removed:
            # Remove unneeded VLANs
            vlan_qs = existent_vlan_qs.filter(vid__in=vlans_to_be_removed)
            obj.tagged_vlans.remove(*vlan_qs)

        obj.mode = mode
        obj.save()

    if untagged_vlan and mode in ["tagged", "access"]:
        # Get current VLAN IDs and compare them with untagged_vlan
        if not obj.untagged_vlan or obj.untagged_vlan != untagged_vlan:
            # A VLAN with a different VLAN ID is set
            vlan_qs = vlan.get_list(vid=untagged_vlan)
            if vlan_qs:
                vlan_o = vlan_qs.pop()
            else:
                # VLAN does not exist, creating one with default name
                vlan_o = vlan.create(vid=untagged_vlan, name=f"VLAN{untagged_vlan:04d}")
            data = {
                "mode": mode,
                "untagged_vlan": vlan_o,
            }
            obj = utils.object_update(obj, **data, force=False)

    return obj


def update_addresses(obj, ip_addresses=None):
    """Update Interface IP Addresses."""
    previous_ip_addresses_qs = obj.ip_addresses.all()
    previous_ip_addresses = [str(ip.address) for ip in previous_ip_addresses_qs]
    site_id = obj.virtual_machine.site.id if obj.virtual_machine.site else None
    vrf_id = obj.vrf.id if obj.vrf else None

    for ip_address in ip_addresses:
        if not ip_address:
            # Skip empty IP addresses
            continue
        # Get or create Prefix
        prefix_o = prefix.get(prefix=ip_address, vrf_id=vrf_id)
        if not prefix_o:
            prefix.create(prefix=ip_address, vrf_id=vrf_id, site_id=site_id)

        if ip_address not in previous_ip_addresses:
            # Get or create IPAddress
            ip_address_list = ipaddress.get_list(address=ip_address, vrf_id=vrf_id)
            if ip_address_list:
                ip_address_o = ip_address_list.pop()
            else:
                ip_address_o = ipaddress.create(address=ip_address, vrf_id=vrf_id)

            # Add missing IP address
            obj.ip_addresses.add(ip_address_o)

    for ip_address in previous_ip_addresses_qs:
        if str(ip_address) not in ip_addresses:
            # Get Interface IP Address objects
            ip_address_o = obj.ip_addresses.get(
                address__net_contains_or_equals=ip_address
            )
            # Remove unconfigured IP Address
            obj.ip_addresses.remove(ip_address_o)

    obj.save()
    return obj
