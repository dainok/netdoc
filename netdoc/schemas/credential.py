"""Schema validation for Credential."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from netdoc.models import Credential

from netdoc import utils


def get_schema():
    """Return the JSON schema to validate Credential data."""
    return {
        "type": "object",
        "properties": {
            "enable_password": {
                "type": "string",
            },
            "name": {
                "type": "string",
            },
            "password": {
                "type": "string",
            },
            "username": {
                "type": "string",
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new Credential objects."""
    schema = get_schema()
    schema["required"] = [
        "name",
    ]
    return schema


def get(name):
    """Return a Credential given name."""
    obj = utils.object_get_or_none(Credential, name=name)
    return obj


def get_or_create(name, **kwargs):
    """Get or create a Credential."""
    created = False
    data = {
        **kwargs,
        "name": name,
    }
    data = utils.delete_empty_keys(data)
    validate(data, get_schema_create(), format_checker=FormatChecker())

    obj = utils.object_get_or_none(Credential, name=name)
    if not obj:
        obj = utils.object_create(Credential, name=name, **kwargs)
        created = True

    return obj, created


def get_list(**kwargs):
    """Get a list of Credential objects."""
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(Credential, **kwargs)
    return result
