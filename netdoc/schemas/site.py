"""Schema validation for Site."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from dcim.models import Site

from netdoc import utils


def get_schema():
    """Return the JSON schema to validate Site data."""
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
            },
            "description": {
                "type": "string",
            },
        },
    }


def get(name):
    """Return a Site."""
    obj = utils.object_get_or_none(Site, name=name)
    return obj


def get_list(**kwargs):
    """Get a list of Site objects."""
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(Site, **kwargs)
    return result
