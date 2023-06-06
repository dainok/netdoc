"""Schema validation for Cable/CableTermination."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from django.conf import settings
from django.db.utils import IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from dcim.models import Interface as Interface_model, Cable, CableTermination

from netdoc.schemas import interface

PLUGIN_SETTINGS = settings.PLUGINS_CONFIG.get("netdoc", {})
TERMINATION_TYPE = ContentType.objects.get(model="interface")


def get_schema():
    """Return the JSON schema to validate ArpTableEntry data."""
    return {
        "type": "object",
        "properties": {
            "left_interface_id": {
                "type": "integer",
                "enum": list(
                    Interface_model.objects.all().values_list("id", flat=True)
                ),
            },
            "right_interface_id": {
                "type": "integer",
                "enum": list(
                    Interface_model.objects.all().values_list("id", flat=True)
                ),
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new ArpTableEntry objects."""
    schema = get_schema()
    schema["required"] = [
        "left_interface_id",
        "right_interface_id",
    ]
    return schema


def sort_interfaces(**kwargs):
    """Neighborship must be sorted by Device name than Interface label.

    Ordered Interface obhects are returned.
    """
    # Get Interface objects
    left_interface_o = interface.get_list(id=kwargs.get("left_interface_id")).pop()
    right_interface_o = interface.get_list(id=kwargs.get("right_interface_id")).pop()

    if left_interface_o.device.name < right_interface_o.device.name:
        # Hostname comparison
        return left_interface_o, right_interface_o
    if left_interface_o.device.name > right_interface_o.device.name:
        # Hostname comparison
        return right_interface_o, left_interface_o
    if left_interface_o.name < right_interface_o.name:
        # Interface comparison
        return left_interface_o, right_interface_o
    # Interface names cannot be equal
    return right_interface_o, left_interface_o


def link(protocol=None, **kwargs):
    """Link two Interface objects.

    Both Interface objects must not be already linked.
    """
    protocol = protocol.upper()
    validate(kwargs, get_schema_create(), format_checker=FormatChecker())

    # Sort interfaces
    left_interface_o, right_interface_o = sort_interfaces(**kwargs)

    try:
        cable_o = Cable.objects.filter(terminations__interface=left_interface_o).get(
            terminations__interface=right_interface_o
        )
    except Cable.DoesNotExist:  # pylint: disable=no-member
        # Create Cable and CableTermination objects
        try:
            with transaction.atomic():
                # To avoid TransactionManagementError those must be executed together
                cable_o = Cable.objects.create()
                CableTermination.objects.create(
                    termination=left_interface_o, cable=cable_o, cable_end="A"
                )
                CableTermination.objects.create(
                    termination=right_interface_o, cable=cable_o, cable_end="B"
                )

            # Trigger Cable update
            cable_o._terminations_modified = True  # pylint: disable=protected-access
            cable_o.full_clean()
            cable_o.save()
        except IntegrityError as exc:
            # L2 connections with multiple devices (do we have a hub or a CDP/LLDP
            # forwarding device?)
            if PLUGIN_SETTINGS.get(f"RAISE_ON_{protocol}_FAIL"):
                raise IntegrityError(
                    f"Multiple neighbors on {left_interface_o.device}:{left_interface_o}"
                    + f" or {right_interface_o.device}:{right_interface_o}"
                ) from exc


def unlink(**kwargs):
    """Unlink two Interface objects."""
    validate(kwargs, get_schema_create(), format_checker=FormatChecker())

    # Sort interfaces
    left_interface_o, right_interface_o = sort_interfaces(**kwargs)

    try:
        cable_o = Cable.objects.filter(terminations__interface=left_interface_o).get(
            terminations__interface=right_interface_o
        )
        cable_o.delete()
    except Cable.DoesNotExist:  # pylint: disable=no-member
        pass
    except IntegrityError as exc:
        raise IntegrityError(
            f"Multiple neighbors on {left_interface_o} or {right_interface_o}"
        ) from exc
