"""Schema validation for Device."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from jsonschema import validate, FormatChecker

from dcim.models import (
    DeviceRole as DeviceRole_model,
    DeviceType as DeviceType_model,
    Manufacturer as Manufacturer_model,
    Site,
    Device,
)
from virtualization.models import Cluster

from netdoc import utils
from netdoc.schemas import manufacturer as manufacturer_api, devicerole, devicetype


def get_schema():
    """Return the JSON schema to validate Device data."""
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "transform": ["toUpperCase"],
            },
            "device_role_id": {
                "type": "integer",
                "enum": list(
                    DeviceRole_model.objects.all().values_list("id", flat=True)
                ),
            },
            "manufacturer_id": {
                "type": "integer",
                "enum": list(
                    Manufacturer_model.objects.all().values_list("id", flat=True)
                ),
            },
            "device_type_id": {
                "type": "integer",
                "enum": list(
                    DeviceType_model.objects.all().values_list("id", flat=True)
                ),
            },
            "serial": {
                "type": "string",
                "transform": ["toUpperCase"],
            },
            "site_id": {
                "type": "integer",
                "enum": list(Site.objects.all().values_list("id", flat=True)),
            },
            "cluster_id": {
                "type": "integer",
                "enum": list(Cluster.objects.all().values_list("id", flat=True)),
            },
        },
    }


def get_schema_create():
    """Return the JSON schema to validate new Device objects."""
    schema = get_schema()
    schema["required"] = [
        "name",
        "device_role_id",
        "device_type_id",
        "site_id",
    ]
    return schema


def create(manufacturer=None, manufacturer_keyword=None, model_keyword=None, **kwargs):
    """Create a Device.

    A Device is created from hostname only, thus generic
    model/tyoe/manufacturer/role are used. They can be updated later.
    Before need to get or create Manufacturer, DeviceModel, DeviceRole and DeviceType.
    """
    if manufacturer_keyword:
        # Looking for the most similar manufacturer
        manufacturer = utils.find_vendor(manufacturer_keyword)

    if not manufacturer:
        manufacturer = "Unknown"

    model_o = create_manufacturer_and_model(
        manufacturer=manufacturer, model_keyword=model_keyword
    )

    devicerole_o = devicerole.get(name="Unknown")
    if not devicerole_o:
        devicerole_o = devicerole.create(name="Unknown")

    kwargs.update(
        {
            "device_role_id": devicerole_o.id,
            "device_type_id": model_o.id,
        }
    )

    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema_create(), format_checker=FormatChecker())
    obj = utils.object_create(Device, **kwargs)
    return obj


def get(name):
    """Return a Device."""
    obj = utils.object_get_or_none(Device, name=name)
    return obj


def get_list(**kwargs):
    """Get a list of Device objects."""
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    result = utils.object_list(Device, **kwargs)
    return result


def update(obj, manufacturer=None, model_keyword=None, **kwargs):
    """Update a Device."""
    update_always = ["cluster_id"]

    if manufacturer and model_keyword and "Unknown" in obj.device_type.model:
        # Manufacturer and model are set, current model is uknown, adding to update_always
        model_o = create_manufacturer_and_model(
            manufacturer=manufacturer, model_keyword=model_keyword
        )

        kwargs.update(
            {
                "device_type_id": model_o.id,
            }
        )
        update_always.append("device_type_id")

    if not obj.serial:
        # Serial is not set, adding to update_always
        update_always.append("serial")

    kwargs = utils.delete_empty_keys(kwargs)
    validate(kwargs, get_schema(), format_checker=FormatChecker())
    kwargs_always = utils.filter_keys(kwargs, update_always)
    obj = utils.object_update(obj, **kwargs_always, force=True)
    return obj


def update_management(obj, discoverable_ip_address):
    """Update primary IP address if match the Discoverable IP address.

    Return True if management IP is set.
    """
    # Set management IP address
    for interface in obj.interfaces.filter(ip_addresses__isnull=False):
        # For each interface
        for ip_address_o in interface.ip_addresses.all():
            # For each configured IP address
            if discoverable_ip_address == str(ip_address_o.address.ip):
                obj.primary_ip4 = ip_address_o
                obj.save()
                return True
    return False


def create_manufacturer_and_model(manufacturer=None, model_keyword=None):
    """Create Manufacturer and DeviceType (model) based on model keyword.

    Return DeviceType.

    Netbox https://github.com/netbox-community/devicetype-library/ is used.
    """
    netbox_model = None

    if manufacturer and model_keyword:
        netbox_model = utils.find_model(
            manufacturer=manufacturer, keyword=model_keyword
        )

    if not manufacturer:
        # Setting default manufacturer
        manufacturer = "Unknown"

    # Get or create Manufacturer
    manufacturer_o = manufacturer_api.get(name=manufacturer)
    if not manufacturer_o:
        manufacturer_o = manufacturer_api.create(name=manufacturer)

    # Get or create DeviceType (model)
    if netbox_model:
        # Model found in Netbox device library
        devicetype_o = devicetype.get(
            model=netbox_model.get("model"), manufacturer_id=manufacturer_o.id
        )
        if not devicetype_o:
            devicetype_o = devicetype.create(
                model=netbox_model.get("model"),
                slug=netbox_model.get("slug"),
                part_number=netbox_model.get("part_number"),
                u_height=netbox_model.get("u_height"),
                is_full_depth=netbox_model.get("is_full_depth"),
                manufacturer_id=manufacturer_o.id,
            )
    else:
        # Model not found in Netbox device library
        # Get or create a generic model
        model = (
            "Unknown device"
            if manufacturer == "Unknown"
            else f"Unknown {manufacturer} device"
        )
        devicetype_o = devicetype.get(model=model, manufacturer_id=manufacturer_o.id)
        if not devicetype_o:
            devicetype_o = devicetype.create(
                model=model, manufacturer_id=manufacturer_o.id
            )

    return devicetype_o
