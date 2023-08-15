/*
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"
 */

function htmlTitle(html) {
    // Convert HTML in node's title to a document DIV
    container = document.createElement("div");
    container.innerHTML = html;
    return container;
  }

// VisGraph options
function visGraphOptions(physics) {
    var options = {
        interaction: {
            hover: true,
            hoverConnectedEdges: true,
            multiselect: true,
        },
        nodes: {
            shape: 'image',
            size: 35,
            font: {
                multi: "md",
                face: "helvetica",
                color:
                    document.documentElement.dataset.netboxColorMode === "dark"
                        ? "#ffffff"
                        : "#000000",
            },
        },
        edges: {
            length: 100,
            width: 2,
            font: {
                face: "helvetica",
            },
            shadow: {
                enabled: true,
            },
        },
        physics: {
            enabled: physics,
            solver: "forceAtlas2Based",
        },
    }
    return options
}

// Set diagram toggle mode button
function setBtnToggleDiagram(physics) {
    var btnToggleDiagramMode = document.getElementById("btnToggleDiagramMode");
    if (physics) {
        btnToggleDiagramMode.innerHTML = '<i class="mdi mdi-pin"></i> Static';
    } else {
        btnToggleDiagramMode.innerHTML = '<i class="mdi mdi-pin-off"></i> Dynamic';
    }
}

// Get current diagram_id
function getDiagramId() {
    var url = new URL(document.URL);
    var diagram_id = url.pathname.split("/")[4]
    return diagram_id;
}

// Save node positions
function saveNodePositions() {
    // Load CSRF token
    var csrftoken = getCookie('csrftoken')

    var physics = graph.physics.physicsEnabled;
    var diagram_id = getDiagramId();
    var url = "/api/plugins/netdoc/diagram/" + diagram_id + "/";
    var xhr = new XMLHttpRequest();
    xhr.open("PATCH", url);
    xhr.setRequestHeader('X-CSRFToken', csrftoken );
    xhr.setRequestHeader("Accept", "application/json");
    xhr.setRequestHeader("Content-Type", "application/json");

    // Get current data and save
    var data = JSON.stringify({
        "details": {
            "physics": physics,
            "positions": graph.getPositions(),
        },
    });
    xhr.onload = () => {
        // Request finished
        if (xhr.status==200) {
            addMessage("success", "Diagram has been saved");
        } else {
            addMessage("danger", "Failed to save diagram");
        }
    };
    xhr.send(data);
}

// Save node position and disable trigger
function saveNodePositionsOnce() {
    saveNodePositions();
    graph.off("afterDrawing", saveNodePositionsOnce);
}

// On page load
window.addEventListener("load", () => {
    // Load topology data from Django
    const topology_data = JSON.parse(document.getElementById("topology_data_json").textContent);
    const topology_details = JSON.parse(document.getElementById("topology_details_json").textContent);
    var physics = "physics" in topology_details ? topology_details["physics"] : true;

    // Set giagram mode button
    setBtnToggleDiagram(physics);

    // For each node/edge, decode HTML title
    for (var i = 0; i < topology_data["nodes"].length; i++) {
        topology_data["nodes"][i]["title"] = htmlTitle(topology_data["nodes"][i]["title"]);
    }
    for (var i = 0; i < topology_data["edges"].length; i++) {
        topology_data["edges"][i]["title"] = htmlTitle(topology_data["edges"][i]["title"]);
    }

    // Get root element
    var container = document.getElementById("visgraph");

    // Draw the diagram
    graph = new vis.Network(container, topology_data, visGraphOptions(physics));
    graph.fit();

    // Save positions once after drawing
    graph.on("afterDrawing", saveNodePositionsOnce);

    // On btnToggleDiagramMode click
    document.getElementById("btnToggleDiagramMode").addEventListener("click", (event) => {
        var new_physics = !graph.physics.physicsEnabled;
        graph.setOptions({ physics: new_physics });
        // Update button
        setBtnToggleDiagram(new_physics);
    });

    // On btnSaveDiagram click
    document.getElementById("btnSaveDiagram").addEventListener("click", () => {
	saveNodePositions();
    });
});
