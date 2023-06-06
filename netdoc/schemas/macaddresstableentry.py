"""Schema validation for MacAddressTableEntry."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from dcim.models import Interface as Interface_model

from netdoc.models import MacAddressTableEntry
from netdoc import utils


def get_schema():
    """Return the JSON schema to validate MacAddressTableEntry data."""
    return {
        "type": "object",
        "properties": {
            "interface_id": {
                "type": "integer",
                "enum": list(
                    Interface_model.objects.all().values_list("id", flat=True)
                ),
            },
            "vvid": {
                "type": "integer",
            },
            "mac_address": {
                "type": "string",
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new MacAddressTableEntry objects."""
    schema = get_schema()
    schema["required"] = [
        "interface_id",
        "vvid",
        "mac_address",
    ]
    return schema


def create(**kwargs):
    """Create an MacAddressTableEntry."""
    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema_create(), format_checker=FormatChecker())
    obj = utils.object_create(MacAddressTableEntry, **kwargs)
    return obj


def get(interface_id, vvid, mac_address, discovered=True):
    """Return an MacAddressTableEntry."""
    obj = utils.object_get_or_none(
        MacAddressTableEntry,
        interface_id=interface_id,
        vvid=vvid,
        mac_address=mac_address,
    )
    if obj and discovered:
        # Update updated_at
        obj.save()
    return obj


def get_list(**kwargs):
    """Get a list of MacAddressTableEntry objects."""
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(MacAddressTableEntry, **kwargs)
    return result
