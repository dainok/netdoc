"""Schema validation for Discoverable."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from django.utils import timezone

from dcim.models import Device, Site

from netdoc.models import Discoverable, Credential, DiscoveryModeChoices
from netdoc import utils


def get_schema():
    """Return the JSON schema to validate Discoverable data."""
    return {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "format": "ipv4",
            },
            "device_id": {
                "type": "integer",
                "enum": list(Device.objects.all().values_list("id", flat=True)),
            },
            "credential_id": {
                "type": "integer",
                "enum": list(Credential.objects.all().values_list("id", flat=True)),
            },
            "discoverable": {
                "type": "boolean",
            },
            "last_discovered_at": {
                "type": "string",
                "format": "date-time",
            },
            "mode": {
                "type": "string",
                "enum": [key for key, value in DiscoveryModeChoices()],
            },
            "site_id": {
                "type": "integer",
                "enum": list(Site.objects.all().values_list("id", flat=True)),
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new Discoverable objects."""
    schema = get_schema()
    schema["required"] = [
        "address",
        "credential_id",
        "mode",
        "site_id",
    ]
    return schema


def create(**kwargs):
    """Create a Discoverable."""
    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema_create(), format_checker=FormatChecker())
    obj = utils.object_create(Discoverable, **kwargs)
    return obj


def get(address, discovered=False):
    """Return a Discoverable given IP address.

    Update last_discovered_at if required.
    """
    obj = utils.object_get_or_none(Discoverable, address=address)
    if obj and discovered:
        obj = utils.object_update(obj, last_discovered_at=timezone.now())
    return obj


def get_list(**kwargs):
    """Get a list of Discoverable objects."""
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(Discoverable, **kwargs)
    return result


def get_or_create(address, **kwargs):
    """Get or create a Discoverable."""
    created = False
    data = {
        **kwargs,
        "address": address,
    }
    data = utils.delete_empty_keys(data)
    validate(data, get_schema_create(), format_checker=FormatChecker())

    obj = utils.object_get_or_none(Discoverable, address=address)
    if not obj:
        obj = utils.object_create(Discoverable, address=address, **kwargs)
        created = True

    return obj, created


def update(obj, **kwargs):
    """Update a Discoverable."""
    update_if_not_set = ["device_id"]
    update_always = ["last_discovered_at"]

    validate(kwargs, get_schema(), format_checker=FormatChecker())
    kwargs_if_not_set = utils.filter_keys(kwargs, update_if_not_set)
    kwargs_always = utils.filter_keys(kwargs, update_always)
    obj = utils.object_update(obj, **kwargs_always, force=True)

    # Before updating device_id we need to check for integrity
    if kwargs_if_not_set.get("device_id"):
        # Check if the device is already associated
        obj_qs = Discoverable.objects.filter(
            device_id=kwargs_if_not_set.get("device_id")
        )
        if obj_qs:
            # A Discoverable with the same address or the same Device ID already exist
            return obj_qs[0]
    obj = utils.object_update(obj, **kwargs_if_not_set, force=False)
    return obj
