"""Functions to build vis.js topology data from a queryset."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import hashlib
import ipaddress
from N2G import drawio_diagram

from jinja2 import Template

from netdoc.models import DeviceImageChoices
from netdoc.utils import DRAWIO_ROLE_MAP

NODE_TEMPLATE = """
<table>
    <tbody>
        <tr>
            <th>Type: </th>
            <td>{{ device.device_type.model }}</td>
        </tr>
        {% if device.primary_ip %}
            <tr>
                <th>IP Address: </th>
                <td>{{ device.primary_ip }}</td>
            </tr>
        {% endif %}
        {% if device.site %}
            <tr>
                <th>Site: </th>
                <td>{{ device.site.name }}</td>
            </tr>
        {% endif %}
        {% if device.location %}
            <tr>
                <th>Location: </th>
                <td>{{ device.location.name }}</td>
            </tr>
        {% endif %}
    </tbody>
</table>
"""

CABLE_TEMPLATE = """
<table>
    <tbody>
        <tr>
            <th>From: </th>
            <td>{{ from_interface.device.name }}:{{ from_interface.name }}</td>
        </tr>
        <tr>
            <th>To: </th>
            <td>{{ to_interface.device.name }}:{{ to_interface.name }}</td>
        </tr>
    </tbody>
</table>
"""

NETWORK_TEMPLATE = """
<table>
    <tbody>
        {% if network %}
        <tr>
            <th>Network: </th>
            <td>{{ network.compressed }}</td>
        </tr>
        <tr>
            <th>VRF: </th>
            <td>{% if vrf %}{{ vrf.name }}{% else %}Global{% endif %}</td>
        </tr>
        {% endif %}
        {% if interface %}
        <tr>
            <th>Interface: </th>
            <td>{{ interface.name }}</td>
        </tr>
        <tr>
            <th>VRF: </th>
            <td>{% if interface.vrf %}{{ interface.vrf.name }}{% else %}Global{% endif %}</td>
        </tr>
        <tr>
            <th>Address: </th>
            <td>{{ address.address }}</td>
        </tr>
        {% endif %}
    </tbody>
</table>
"""


def integer_hash(text, length=16):
    """Return a very simple and insecure interger hash.

    Used in L3 diagrams to link networks with VRF aware devices.
    """
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % 10**length


def get_l2_topology_data(queryset, details):
    """Create a L2 vis.js topology data from an Interface queryset."""
    nodes = {}
    links = {}

    for interface_o in queryset:
        # Create device
        device_o = interface_o.device
        device_id = device_o.pk
        if device_id not in nodes:
            device_role = device_o.device_role.slug
            if device_role in [key for key, value in DeviceImageChoices()]:
                image_url = f"/static/netdoc/img/{device_role}.png"
            else:
                image_url = "/static/netdoc/img/unknown.png"
            nodes[device_id] = {
                "id": device_id,
                "label": interface_o.device.name,
                "role": device_role,
                "image": image_url,
                "shape": "image",
                "title": Template(NODE_TEMPLATE).render(device=device_o),
            }
            # Set position
            if "positions" in details and str(device_id) in details["positions"]:
                nodes[device_id]["x"] = details["positions"][str(device_id)].get("x")
                nodes[device_id]["y"] = details["positions"][str(device_id)].get("y")

        # Create link
        cable_o = interface_o.cable
        cable_id = cable_o.pk
        if cable_id not in links:
            # Add link only if not already added
            from_interface_o = cable_o.terminations.first().interface.first()
            to_interface_o = cable_o.terminations.last().interface.first()
            if (
                from_interface_o.device.pk in nodes
                and to_interface_o.device.pk in nodes
            ):
                # Add link only if both nodes are in the query
                links[cable_id] = {
                    "id": cable_id,
                    "from": from_interface_o.device.pk,
                    "from_label": from_interface_o.label,
                    "to": to_interface_o.device.pk,
                    "to_label": to_interface_o.label,
                    "title": Template(CABLE_TEMPLATE).render(
                        from_interface=from_interface_o, to_interface=to_interface_o
                    ),
                }

    return {
        "nodes": list(nodes.values()),
        "edges": list(links.values()),
    }


def get_l2_drawio_topology(queryset, diagram):
    """Create a L2 DrawIO topology data from an Interface queryset."""
    data = get_l2_topology_data(queryset, diagram.details)
    nodes = data.get("nodes")
    links = data.get("edges")

    # Transform node list into dict using id a key
    nodes_dict = {item["id"]: item for item in nodes}

    # Create diagram
    drawio_o = drawio_diagram()
    drawio_o.add_diagram("Page-1")

    for node in nodes:
        # Add node
        node_label = node.get("label")
        node_style = (
            node.get("role") if node.get("role") in DRAWIO_ROLE_MAP else "unknown"
        )
        drawio_o.add_node(
            id=node_label,
            url="Page-1",
            x_pos=node.get("x") if node.get("x") else None,
            y_pos=node.get("y") if node.get("x") else None,
            **DRAWIO_ROLE_MAP[node_style],
        )

    for link in links:
        # Add link (using node labels)
        drawio_o.add_link(
            nodes_dict[link["from"]]["label"],
            nodes_dict[link["to"]]["label"],
            src_label=link["from_label"],
            trgt_label=link["to_label"],
            link_id=link["id"],
        )

    return drawio_o.dump_xml()


def get_l3_topology_data(queryset, details):
    """Create a L3 vis.js topology data from an Interface queryset."""
    nodes = {}
    networks = {}
    links = {}

    for interface_o in queryset:
        for address_o in interface_o.ip_addresses.all():
            # We are using IPAddress's VRF. Interface's VRF is not relevant
            # Create device
            vrf_name = interface_o.vrf.name if interface_o.vrf else None
            device_o = interface_o.device
            device_name = device_o.name
            device_str = f"{device_name}:{vrf_name}" if vrf_name else device_name
            device_id = integer_hash(device_str)
            if device_id not in nodes:
                device_role = device_o.device_role.slug
                if device_role in [key for key, value in DeviceImageChoices()]:
                    image_url = f"/static/netdoc/img/{device_role}.png"
                else:
                    image_url = "/static/netdoc/img/unknown.png"
                nodes[device_id] = {
                    "id": device_id,
                    "label": device_str,
                    "role": device_role,
                    "image": image_url,
                    "shape": "image",
                    "title": Template(NODE_TEMPLATE).render(device=device_o),
                }
                # Set position
                if "positions" in details and str(device_id) in details["positions"]:
                    nodes[device_id]["x"] = details["positions"][str(device_id)].get(
                        "x"
                    )
                    nodes[device_id]["y"] = details["positions"][str(device_id)].get(
                        "y"
                    )

            # Create network
            network_o = ipaddress.ip_interface(address_o.address).network
            network_str = str(network_o.network_address.compressed)
            network_id = integer_hash(network_str)
            if network_id not in networks:
                networks[network_id] = {
                    "id": network_id,
                    "name": network_o.compressed,
                    "label": network_o.compressed,
                    "title": Template(NETWORK_TEMPLATE).render(
                        network=network_o, vrf=address_o.vrf
                    ),
                    "shape": "box",
                    "borderWidth": 2,
                    "color": {
                        "border": "#1b9bd0",
                        "background": "#36c6f4",
                        "highlight": {"border": "#1b9bd0", "background": "#36c6f4"},
                        "hover": {"border": "#1b9bd0", "background": "#36c6f4"},
                    },
                    "font": {
                        "color": "#000000",
                        "size": 14,
                    },
                }
                # Set position
                if "positions" in details and str(network_id) in details["positions"]:
                    networks[network_id]["x"] = details["positions"][
                        str(network_id)
                    ].get("x")
                    networks[network_id]["y"] = details["positions"][
                        str(network_id)
                    ].get("y")

            # Create link (Interface to Network)
            link_id = f"{device_id}-{network_id}"
            if link_id not in links and device_id in nodes and network_id in networks:
                # Add link only if not already added and if
                # device_id and network_id are in the query
                links[link_id] = {
                    "id": link_id,
                    "from": device_id,
                    "from_label": str(address_o.address),
                    "to": network_id,
                    "title": Template(NETWORK_TEMPLATE).render(
                        interface=interface_o, address=address_o
                    ),
                }

    return {
        "nodes": list(nodes.values()) + list(networks.values()),
        "edges": list(links.values()),
    }


def get_l3_drawio_topology(queryset, diagram):
    """Create a L3 DrawIO topology data from an Interface queryset."""
    data = get_l3_topology_data(queryset, diagram.details)
    nodes = data.get("nodes")
    links = data.get("edges")

    # Transform node list into dict using id a key
    nodes_dict = {item["id"]: item for item in nodes}

    # Create diagram
    drawio_o = drawio_diagram()
    drawio_o.add_diagram("Page-1")

    for node in nodes:
        # Add node
        node_label = node.get("label")
        node_style = (
            node.get("role") if node.get("role") in DRAWIO_ROLE_MAP else "unknown"
        )
        node_shape = node.get("shape")
        if node_shape == "image":
            # Device (using image/icon)
            drawio_o.add_node(
                id=node_label,
                url="Page-1",
                x_pos=node.get("x") if node.get("x") else None,
                y_pos=node.get("y") if node.get("x") else None,
                **DRAWIO_ROLE_MAP[node_style],
            )
        else:
            # Network (using a simple box)
            drawio_o.add_node(
                id=node_label,
                url="Page-1",
                width="80",
                height="30",
                x_pos=node.get("x") if node.get("x") else None,
                y_pos=node.get("y") if node.get("x") else None,
            )

    for link in links:
        # Add link (using node labels)
        drawio_o.add_link(
            nodes_dict[link["from"]]["label"],
            nodes_dict[link["to"]]["label"],
            src_label=link["from_label"],
            link_id=link["id"],
        )

    return drawio_o.dump_xml()
