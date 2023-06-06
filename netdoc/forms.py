"""Forms, called by Views."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from django import forms

from dcim.models import Device, Site, DeviceRole
from ipam.models import VRF

from utilities.forms import (
    CSVModelChoiceField,
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    StaticSelect,
    BOOLEAN_WITH_BLANK_CHOICES,
    add_blank_choice,
)
from netbox.forms import (
    NetBoxModelForm,
    NetBoxModelFilterSetForm,
    NetBoxModelCSVForm,
    NetBoxModelBulkEditForm,
)

from netdoc.models import (
    Credential,
    Discoverable,
    DiscoveryLog,
    DiscoveryModeChoices,
    DiagramModeChoices,
)

#
# Credential forms
#


class CredentialForm(NetBoxModelForm):
    """Form used to add/edit Credential."""

    username = forms.CharField(required=False)
    password = forms.CharField(required=False, widget=forms.PasswordInput)
    enable_password = forms.CharField(required=False, widget=forms.PasswordInput)

    class Meta:
        """Form metadata."""

        model = Credential
        fields = [
            "name",
            "username",
            "password",
            "enable_password",
            "tags",
        ]


class CredentialCSVForm(NetBoxModelCSVForm):
    """Form used to add Credential objects via CSV import."""

    class Meta:
        """Form metadata."""

        model = Credential
        fields = ["name", "username", "password", "enable_password"]


class CredentialBulkEditForm(NetBoxModelBulkEditForm):
    """Form used to bulk edit Credential objects."""

    username = forms.CharField(required=False)
    password = forms.CharField(required=False, widget=forms.PasswordInput)
    enable_password = forms.CharField(required=False, widget=forms.PasswordInput)

    model = Credential
    nullable_fields = ["username", "password", "enable_password"]


#
# Diagram forms
#


class DiagramForm(NetBoxModelForm):
    """Form used to add/edit Diagram."""

    name = forms.CharField(required=False)
    mode = forms.ChoiceField(choices=DiagramModeChoices, required=True)
    vrfs = DynamicModelMultipleChoiceField(
        queryset=VRF.objects.all(),
        required=False,
    )
    include_global_vrf = forms.BooleanField(
        required=False,
        initial=False,
        help_text="If set and no VRF is selected, Global only is included."
        + " If set and VRFs are selected, Global is included.",
    )
    sites = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False,
    )
    device_roles = DynamicModelMultipleChoiceField(
        queryset=DeviceRole.objects.all(),
        required=False,
    )

    class Meta:
        """Form metadata."""

        model = Credential
        fields = [
            "name",
            "mode",
            "device_roles",
            "sites",
            "vrfs",
            "include_global_vrf",
            "tags",
        ]


#
# Discoverable views
#


class DiscoverableForm(NetBoxModelForm):
    """Form used to add/edit Discoverable."""

    address = forms.GenericIPAddressField()
    credential = forms.ModelChoiceField(
        queryset=Credential.objects.all(),
        required=True,
    )
    mode = forms.ChoiceField(choices=DiscoveryModeChoices, required=True)
    device = DynamicModelChoiceField(queryset=Device.objects.all(), required=False)
    discoverable = forms.BooleanField(
        required=False,
        initial=True,
    )
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        help_text="Site",
        required=True,
    )

    class Meta:
        """Form metadata."""

        model = Discoverable
        fields = [
            "address",
            "device",
            "credential",
            "mode",
            "discoverable",
            "site",
            "tags",
        ]


class DiscoverableCSVForm(NetBoxModelCSVForm):
    """Form used to add Discoverable objects via CSV import."""

    address = forms.GenericIPAddressField(
        help_text="Management IP address",
    )
    credential = CSVModelChoiceField(
        queryset=Credential.objects.all(),
        required=True,
        to_field_name="name",
        help_text="Assigned credential",
    )
    mode = forms.ChoiceField(
        choices=DiscoveryModeChoices,
        required=True,
        help_text="Discovery mode",
    )
    site = CSVModelChoiceField(
        queryset=Site.objects.all(),
        to_field_name="name",
        help_text="Site",
        required=True,
    )

    class Meta:
        """Form metadata."""

        model = Discoverable
        fields = ["address", "credential", "mode", "site"]


class DiscoverableBulkEditForm(NetBoxModelBulkEditForm):
    """Form used to bulk edit Discoverable objects."""

    credential = CSVModelChoiceField(
        queryset=Credential.objects.all(),
        required=False,
        to_field_name="name",
        help_text="Assigned credential",
    )
    mode = forms.ChoiceField(
        choices=add_blank_choice(DiscoveryModeChoices),
        required=False,
        initial="",
        widget=StaticSelect(),
        help_text="Discovery mode",
    )
    discoverable = forms.NullBooleanField(
        help_text="Is discoverable?",
        required=False,
    )
    site = forms.ModelChoiceField(
        queryset=Site.objects.all(),
        to_field_name="name",
        help_text="Site",
        required=False,
    )

    model = Discoverable
    nullable_fields = "device"


class DiscoveryLogListFilterForm(NetBoxModelFilterSetForm):
    """Form used to filter DiscoveryLog using parameters. Used in DiscoveryLogListView."""

    model = DiscoveryLog
    configuration = forms.NullBooleanField(
        required=False,
        label="Configuration output",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    success = forms.NullBooleanField(
        required=False,
        label="Completed successfully",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    supported = forms.NullBooleanField(
        required=False,
        label="Command is supported",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    parsed = forms.NullBooleanField(
        required=False,
        label="Parsed successfully",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    ingested = forms.NullBooleanField(
        required=False,
        label="Ingested successfully",
        widget=StaticSelect(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
