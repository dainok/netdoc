"""Schema validation for ClusterType."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from virtualization.models import ClusterType

from netdoc import utils


def get_schema():
    """Return the JSON schema to validate ClusterType data."""
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new ClusterType objects."""
    schema = get_schema()
    schema["required"] = [
        "name",
    ]
    return schema


def create(**kwargs):
    """Create a ClusterType."""
    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema_create(), format_checker=FormatChecker())
    obj = utils.object_create(ClusterType, **kwargs)
    return obj


def get(name):
    """Return a ClusterType."""
    obj = utils.object_get_or_none(ClusterType, name=name)
    return obj


def get_list(**kwargs):
    """Get a list of ClusterType objects."""
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(ClusterType, **kwargs)
    return result
