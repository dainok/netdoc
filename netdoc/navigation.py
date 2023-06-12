"""Sidebar navigation buttons."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from extras.plugins import PluginMenuButton, PluginMenuItem, PluginMenu
from utilities.choices import ButtonColorChoices

credential_buttons = [
    PluginMenuButton(
        link="plugins:netdoc:credential_add",
        title="Add",
        icon_class="mdi mdi-plus-thick",
        color=ButtonColorChoices.GREEN,
    ),
    PluginMenuButton(
        link="plugins:netdoc:credential_import",
        title="Import",
        icon_class="mdi mdi-upload",
        color=ButtonColorChoices.CYAN,
    ),
]

diagram_buttons = [
    PluginMenuButton(
        link="plugins:netdoc:diagram_add",
        title="Add",
        icon_class="mdi mdi-plus-thick",
        color=ButtonColorChoices.GREEN,
    ),
]

discoverable_buttons = [
    PluginMenuButton(
        link="plugins:netdoc:discoverable_add",
        title="Add",
        icon_class="mdi mdi-plus-thick",
        color=ButtonColorChoices.GREEN,
    ),
    PluginMenuButton(
        link="plugins:netdoc:discoverable_import",
        title="Import",
        icon_class="mdi mdi-upload",
        color=ButtonColorChoices.CYAN,
    ),
]

menu_discovery = (
    PluginMenuItem(
        link="plugins:netdoc:credential_list",
        link_text="Credentials",
        buttons=credential_buttons,
        permissions=["netdoc.view_credential"],
    ),
    PluginMenuItem(
        link="plugins:netdoc:discoverable_list",
        link_text="Discoverables",
        buttons=discoverable_buttons,
        permissions=["netdoc.view_discoverable"],
    ),
    PluginMenuItem(
        link="plugins:netdoc:discoverylog_list",
        link_text="Logs",
        permissions=["netdoc.view_discoverylog"],
    ),
)

menu_tables = (
    PluginMenuItem(
        link="plugins:netdoc:arptableentry_list",
        link_text="ARP Table",
        permissions=["netdoc.view_arptableentry"],
    ),
    PluginMenuItem(
        link="plugins:netdoc:macaddresstableentry_list",
        link_text="MAC Address Table",
        permissions=["netdoc.view_macaddresstableentry"],
    ),
    PluginMenuItem(
        link="plugins:netdoc:routetableentry_list",
        link_text="Routing Table",
        permissions=["netdoc.view_routingtableentry"],
    ),
)

menu = PluginMenu(
    label="NetDoc",
    groups=(
        (
            "Diagrams",
            (
                PluginMenuItem(
                    link="plugins:netdoc:diagram_list",
                    link_text="Diagrams",
                    buttons=diagram_buttons,
                    permissions=["netdoc.view_diagram"],
                ),
            ),
        ),
        ("Discovery", menu_discovery),
        ("Tables", menu_tables),
    ),
)
