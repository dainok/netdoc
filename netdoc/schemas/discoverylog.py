"""Schema validation for DiscoveryLog."""

__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from netdoc.models import DiscoveryLog, Discoverable
from netdoc import utils


def get_schema():
    """Return the JSON schema to validate DiscoveryLog data."""
    return {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
            },
            "configuration": {
                "type": "boolean",
            },
            "details": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                    },
                    "enable": {
                        "type": "boolean",
                    },
                    "order": {
                        "type": "integer",
                    },
                    "template": {
                        "type": "string",
                    },
                    "supported": {
                        "type": "boolean",
                    },
                },
                "required": [
                    "command",
                    "enable",
                    "order",
                    "template",
                ],
            },
            "discoverable_id": {
                "type": "integer",
                "enum": list(Discoverable.objects.all().values_list("id", flat=True)),
            },
            "parsed_output": {
                "type": ["object", "array", "string"],
            },
            "raw_output": {
                "type": "string",
            },
            "template": {
                "type": "string",
            },
            "success": {
                "type": "boolean",
            },
            "parsed": {
                "type": "boolean",
            },
            "ingested": {
                "type": "boolean",
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new DiscoveryLog objects."""
    schema = get_schema()
    schema["required"] = [
        "command",
        "details",
        "discoverable_id",
        "raw_output",
        "template",
    ]
    return schema


def create(**kwargs):
    """Create a DiscoveryLog."""
    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema_create(), format_checker=FormatChecker())
    obj = utils.object_create(DiscoveryLog, **kwargs)
    return obj


def get_list(**kwargs):
    """Get a list of DiscoveryLog objects."""
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(DiscoveryLog, **kwargs)
    return result


def update(obj, **kwargs):
    """Update a DiscoveryLog."""
    update_always = ["parsed_output", "parsed", "ingested"]

    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    kwargs_always = utils.filter_keys(kwargs, update_always)
    obj = utils.object_update(obj, **kwargs_always, force=True)
    return obj
