"""Schema validation for VRF."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from ipam.models import VRF

from netdoc import utils


def get_schema():
    """Return the JSON schema to validate VRF data."""
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
            },
            "rd": {
                "type": "string",
            },
            "mandatory_rd": {
                "type": "boolean",
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new VRF objects."""
    schema = get_schema()
    schema["required"] = [
        "name",
    ]
    return schema


def create(mandatory_rd=True, **kwargs):
    """Create an VRF."""
    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema_create(), format_checker=FormatChecker())
    if not mandatory_rd and kwargs.get("rd"):
        # RD must be unique on Netbox, if a VRF exist with the same RD,
        # RD is removed to avoid database key error
        vrf_list = get_list(rd=kwargs.get("rd"))
        if vrf_list and kwargs.get("name") != vrf_list[0].name:
            # Duplicated RD with different VRF name
            del kwargs["rd"]
    obj = utils.object_create(VRF, **kwargs)
    return obj


def get(name):
    """Return an VRF."""
    obj = utils.object_get_or_none(VRF, name=name)
    return obj


def get_list(**kwargs):
    """Get a list of VRF objects."""
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(VRF, **kwargs)
    return result


def get_or_create(name, **kwargs):
    """Get or create a VRF."""
    created = False
    data = {
        **kwargs,
        "name": name,
    }
    data = utils.delete_empty_keys(data)
    validate(data, get_schema_create(), format_checker=FormatChecker())

    obj = utils.object_get_or_none(VRF, name=name)
    if not obj:
        obj = utils.object_create(VRF, name=name, **kwargs)
        created = True

    return obj, created


def update(obj, mandatory_rd=True, **kwargs):
    """Update an VRF."""
    update_if_not_set = ["rd"]

    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    if not mandatory_rd and kwargs.get("rd"):
        # RD must be unique on Netbox, if a VRF exist with the same RD,
        # RD is removed to avoid database key error
        vrf_list = get_list(rd=kwargs.get("rd"))
        if vrf_list and kwargs.get("name") != vrf_list[0].name:
            # Duplicated RD with different VRF name
            del kwargs["rd"]
    kwargs_if_not_set = utils.filter_keys(kwargs, update_if_not_set)
    obj = utils.object_update(obj, **kwargs_if_not_set, force=False)
    return obj
