"""Schema validation for ArpTableEntry."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import ipaddress
from jsonschema import validate, FormatChecker

from dcim.models import Site
from ipam.models import Prefix, VRF

from netdoc import utils


def get_schema():
    """Return the JSON schema to validate Prefix data."""
    return {
        "type": "object",
        "properties": {
            "prefix": {
                "type": "string",
            },
            "vrf_id": {
                "type": "integer",
                "enum": list(VRF.objects.all().values_list("id", flat=True)),
            },
            "site_id": {
                "type": "integer",
                "enum": list(Site.objects.all().values_list("id", flat=True)),
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new Prefix objects."""
    schema = get_schema()
    schema["required"] = [
        "prefix",
    ]
    return schema


def address_to_network(address):
    """Convert an IP address with mask into the network address with mask."""
    try:
        # It's a network
        return str(ipaddress.ip_network(address))
    except ValueError:
        # It's a host
        try:
            return str(ipaddress.ip_interface(address).network)
        except ValueError as exc:
            raise ValueError(f"Invalid IP address {address}") from exc


def create(prefix=None, **kwargs):
    """Create an Prefix."""
    prefix = address_to_network(prefix)
    data = {
        "prefix": prefix,
        **kwargs,
    }
    data = utils.delete_empty_keys(data)
    validate(data, get_schema_create(), format_checker=FormatChecker())
    obj = utils.object_create(Prefix, **data)
    return obj


def get(prefix, vrf_id=None):
    """Return an Prefix."""
    prefix = address_to_network(prefix)
    obj = utils.object_get_or_none(Prefix, prefix=prefix, vrf__id=vrf_id)
    return obj
