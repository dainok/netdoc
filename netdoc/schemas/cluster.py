"""Schema validation for Cluster."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from virtualization.models import Cluster, ClusterType as ClusterType_model

from netdoc import utils


def get_schema():
    """Return the JSON schema to validate Cluster data."""
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
            },
            "type_id": {
                "type": "integer",
                "enum": list(
                    ClusterType_model.objects.all().values_list("id", flat=True)
                ),
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new Cluster objects."""
    schema = get_schema()
    schema["required"] = [
        "name",
        "type_id",
    ]
    return schema


def create(**kwargs):
    """Create a Cluster."""
    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema_create(), format_checker=FormatChecker())
    obj = utils.object_create(Cluster, **kwargs)
    return obj


def get(name):
    """Return a VirtualMachine."""
    obj = utils.object_get_or_none(Cluster, name=name)
    return obj


def get_list(**kwargs):
    """Get a list of VirtualMachine objects."""
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(Cluster, **kwargs)
    return result


def update(obj, status=None, **kwargs):
    """Update a VirtualMachine."""
    update_always = [
        "device_id",
        "vcpu",
        "memory",
        "disk",
    ]

    if status and obj.status not in ["active", "offline"]:
        # Status is set and current status is not active or offline, adding to update_always
        kwargs.update(
            {
                "status": status,
            }
        )
        update_always.append("status")

    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    kwargs_always = utils.filter_keys(kwargs, update_always)
    obj = utils.object_update(obj, **kwargs_always, force=True)
    return obj
