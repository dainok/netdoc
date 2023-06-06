"""Schema validation for ArpTableEntry."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from ipam.models import IPAddress, VRF

from netdoc import utils


def get_schema():
    """Return the JSON schema to validate IPAddress data."""
    return {
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
            },
            "vrf_id": {
                "type": "integer",
                "enum": list(VRF.objects.all().values_list("id", flat=True)),
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new IPAddress objects."""
    schema = get_schema()
    schema["required"] = [
        "address",
    ]
    return schema


def create(**kwargs):
    """Create an IPAddress."""
    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema_create(), format_checker=FormatChecker())
    obj = utils.object_create(IPAddress, **kwargs)
    return obj


def get_list(**kwargs):
    """Get a list of IPAddress objects."""
    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(IPAddress, **kwargs)
    return result
