"""Advanced filters."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from django import template
from django.urls import reverse

from utilities.utils import get_viewname

register = template.Library()


@register.inclusion_tag("netdoc/buttons/discover.html")
def discover_button(instance):
    """Add discover button.

    Used in templates/netdoc.
    """
    viewname = get_viewname(instance, "discover")
    url = reverse(viewname, kwargs={"pk": instance.pk})

    return {
        "url": url,
    }


@register.inclusion_tag("netdoc/buttons/export.html")
def export_button(instance):
    """Add export button.

    Used in templates/netdoc.
    """
    viewname = get_viewname(instance, "export")
    url = reverse(viewname, kwargs={"pk": instance.pk})

    return {
        "url": url,
    }
