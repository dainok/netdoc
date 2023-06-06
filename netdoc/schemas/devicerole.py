"""Schema validation for DeviceRole."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker
from slugify import slugify

from dcim.models import DeviceRole

from netdoc import utils


def get_schema():
    """Return the JSON schema to validate DeviceRole data."""
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
            },
            "vm_role": {
                "type": "boolean",
            },
            "description": {
                "type": "string",
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new DeviceRole objects."""
    schema = get_schema()
    schema["required"] = [
        "name",
    ]
    return schema


def create(**kwargs):
    """Create a DeviceRole."""
    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema_create(), format_checker=FormatChecker())
    kwargs["slug"] = slugify(kwargs.get("name"))
    obj = utils.object_create(DeviceRole, **kwargs)
    return obj


def get(name):
    """Return a DeviceRole."""
    obj = utils.object_get_or_none(DeviceRole, name=name)
    return obj


def get_list(**kwargs):
    """Get a list of DeviceRole objects."""
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(DeviceRole, **kwargs)
    return result
