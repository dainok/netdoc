"""Schema validation for VLAN."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from ipam.models import VLAN
from ipam.choices import VLANStatusChoices

from netdoc import utils


def get_schema():
    """Return the JSON schema to validate VLAN data."""
    return {
        "type": "object",
        "properties": {
            "vid": {
                "type": "integer",
            },
            "name": {
                "type": "string",
            },
            "status": {
                "type": "string",
                "enum": [key for key, value in VLANStatusChoices()],
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new VLAN objects."""
    schema = get_schema()
    schema["required"] = [
        "vid",
        "name",
        "status",
    ]
    return schema


def create(status="active", **kwargs):
    """Create an VLAN."""
    data = {
        **kwargs,
        "status": status,  # Default status is active
    }
    data = utils.delete_empty_keys(data)
    validate(data, get_schema_create(), format_checker=FormatChecker())
    obj = utils.object_create(VLAN, **data)
    return obj


def get(vid, name):
    """Return an VLAN."""
    obj = utils.object_get_or_none(VLAN, vid=vid, name=name)
    return obj


def get_list(**kwargs):
    """Get a list of VLAN objects."""
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(VLAN, **kwargs)
    return result
