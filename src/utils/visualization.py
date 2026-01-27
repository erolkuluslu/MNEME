"""
Knowledge Graph Visualization Utilities

Interactive PyVis-based visualization for MNEME knowledge graphs.
Supports community coloring, hub/bridge highlighting, and dark mode.
"""

import json
import os
from typing import List, Dict, Any, Optional, Set

try:
    import networkx as nx
except ImportError:
    nx = None

try:
    from pyvis.network import Network
except ImportError:
    Network = None

from src.models.graph import KnowledgeStructures

# Community detection color palette (colorblind-friendly)
COMMUNITY_COLORS = [
    '#e41a1c',  # Red
    '#377eb8',  # Blue
    '#4daf4a',  # Green
    '#984ea3',  # Purple
    '#ff7f00',  # Orange
    '#ffff33',  # Yellow
    '#a65628',  # Brown
    '#f781bf',  # Pink
]


def visualize_mneme_graph(
    graph: "nx.DiGraph",
    structures: Optional[KnowledgeStructures] = None,
    output_file: str = "knowledge_graph.html",
    title: str = "MNEME Knowledge Graph",
    highlight_hubs: bool = True,
    highlight_bridges: bool = True,
    max_nodes: int = 500,
) -> Dict[str, Any]:
    """
    Create interactive PyVis visualization of MNEME knowledge graph.

    Features:
    - Nodes colored by community
    - Hub nodes displayed as stars with larger size
    - Bridge nodes displayed as diamonds
    - Dark mode toggle
    - Physics controls
    - Node filtering and focus
    - Statistics dashboard

    Args:
        graph: NetworkX knowledge graph
        structures: Pre-computed knowledge structures (communities, hubs, bridges)
        output_file: HTML file to save visualization
        title: Title for visualization
        highlight_hubs: Show hubs as stars
        highlight_bridges: Show bridges as diamonds
        max_nodes: Maximum nodes to display (for large graphs)

    Returns:
        Dict with visualization statistics
    """
    if nx is None:
        raise ImportError("networkx is required for visualization")
    if Network is None:
        raise ImportError("pyvis is required for visualization")

    if graph.number_of_nodes() == 0:
        print("No nodes in graph to visualize")
        return {"nodes": 0, "edges": 0, "communities": 0, "output_file": output_file}

    print(f"Creating visualization with {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges...")

    # Limit nodes for large graphs
    if graph.number_of_nodes() > max_nodes:
        print(f"Limiting to top {max_nodes} nodes by degree...")
        graph = _limit_graph_by_degree(graph, max_nodes)

    # Build lookup structures
    hub_ids: Set[str] = set()
    bridge_ids: Set[str] = set()
    node_to_community: Dict[str, int] = {}
    community_summaries: Dict[int, str] = {}

    if structures:
        hub_ids = set(structures.get_hub_ids())
        bridge_ids = set(structures.get_bridge_ids())
        node_to_community = structures.chunk_to_community

        # Get community summaries
        for community in structures.communities:
            if community.summary:
                community_summaries[community.community_id] = community.summary[:200] + "..."

    num_communities = len(set(node_to_community.values())) if node_to_community else 1

    # Calculate node metrics
    degrees = dict(graph.degree())
    max_degree = max(degrees.values()) if degrees else 1

    # Create PyVis network
    net = Network(
        height="100%",
        width="100%",
        directed=True,
        notebook=False,
        cdn_resources='in_line',
        bgcolor="#ffffff",
        font_color=True,
        select_menu=False,
        filter_menu=False,
    )

    # Add nodes with styling
    for node_id in graph.nodes():
        node_data = graph.nodes[node_id]

        # Determine community and color
        community_id = node_to_community.get(node_id, 0)
        color = COMMUNITY_COLORS[community_id % len(COMMUNITY_COLORS)]

        # Determine shape and size
        degree = degrees.get(node_id, 0)
        size = 10 + (25 * degree / max_degree)

        if highlight_hubs and node_id in hub_ids:
            shape = "star"
            size *= 1.5
            border_color = "#000000"
        elif highlight_bridges and node_id in bridge_ids:
            shape = "diamond"
            size *= 1.3
            border_color = "#ffffff"
        else:
            shape = "dot"
            border_color = color

        # Build tooltip
        year = node_data.get("year", "?")
        category = node_data.get("category", "?")
        tooltip_parts = [
            f"ID: {node_id}",
            f"Year: {year}",
            f"Category: {category}",
            f"Degree: {degree}",
            f"Community: {community_id}",
        ]
        if node_id in hub_ids:
            tooltip_parts.append("Role: HUB")
        if node_id in bridge_ids:
            tooltip_parts.append("Role: BRIDGE")

        # Add community summary preview to tooltip
        if community_id in community_summaries:
            tooltip_parts.append(f"\nCluster theme: {community_summaries[community_id]}")

        tooltip = "\n".join(tooltip_parts)

        # Create label (shortened)
        label = node_id[:20] + "..." if len(node_id) > 20 else node_id

        net.add_node(
            node_id,
            label=label,
            title=tooltip,
            color={"background": color, "border": border_color},
            shape=shape,
            size=size,
            font={"color": "#000000", "size": 12},
        )

    # Add edges
    for source, target, edge_data in graph.edges(data=True):
        edge_type = edge_data.get("edge_type", "related")
        weight = edge_data.get("weight", 0.5)

        # Style edges by type
        if edge_type == "cross_domain":
            edge_color = "#ff7f00"
            dashes = True
        elif edge_type == "temporal":
            edge_color = "#984ea3"
            dashes = False
        else:
            edge_color = "#888888"
            dashes = False

        net.add_edge(
            source,
            target,
            title=edge_type,
            color=edge_color,
            width=1 + weight,
            dashes=dashes,
            arrows="to",
        )

    # Set visualization options
    options = _get_vis_options()
    net.set_options(json.dumps(options))

    # Generate HTML
    net.generate_html()
    html = net.html

    # Inject custom template
    html = _inject_custom_template(
        html,
        num_nodes=graph.number_of_nodes(),
        num_edges=graph.number_of_edges(),
        num_communities=num_communities,
        num_hubs=len(hub_ids),
        num_bridges=len(bridge_ids),
        title=title,
    )

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Visualization saved to: {output_file}")

    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "communities": num_communities,
        "hubs": len(hub_ids),
        "bridges": len(bridge_ids),
        "output_file": output_file,
    }


def _limit_graph_by_degree(graph: "nx.DiGraph", max_nodes: int) -> "nx.DiGraph":
    """Limit graph to top-N nodes by degree."""
    degrees = dict(graph.degree())
    sorted_nodes = sorted(degrees.keys(), key=lambda n: degrees[n], reverse=True)
    keep_nodes = set(sorted_nodes[:max_nodes])
    return graph.subgraph(keep_nodes).copy()


def _get_vis_options() -> Dict:
    """Get visualization options for PyVis."""
    return {
        "physics": {
            "enabled": True,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08,
            },
            "stabilization": {"iterations": 200, "enabled": True},
        },
        "edges": {
            "color": {"inherit": False},
            "font": {"size": 10},
            "smooth": {"type": "continuous"},
        },
        "nodes": {
            "font": {"size": 12, "face": "Tahoma"},
            "scaling": {"min": 10, "max": 50},
            "tooltipDelay": 100,
        },
        "interaction": {
            "hover": True,
            "navigationButtons": True,
            "keyboard": True,
            "tooltipDelay": 100,
            "zoomView": True,
        },
        "layout": {"improvedLayout": True},
    }


def _inject_custom_template(
    html: str,
    num_nodes: int,
    num_edges: int,
    num_communities: int,
    num_hubs: int,
    num_bridges: int,
    title: str,
) -> str:
    """Inject custom controls and styling into HTML."""
    import re

    custom_controls = f'''
<div class="card" style="width: 100%; height: 100vh; display: flex; flex-direction: column;">
    <div id="graph-controls" style="margin: 10px; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
        <div>
            <button onclick="togglePhysics()" id="physics-toggle" class="btn btn-primary">Disable Physics</button>
            <button onclick="togglePhysicsSettings()" id="physics-settings-toggle" class="btn btn-outline-info">Physics Settings</button>
            <button onclick="stabilizeNetwork()" class="btn btn-secondary">Stabilize</button>
            <button onclick="toggleDarkMode()" id="theme-toggle" class="btn btn-info">Dark Mode</button>
            <button onclick="toggleFilters()" id="filter-toggle" class="btn btn-outline-info">Show Filters</button>
            <button onclick="toggleLabels()" id="labels-toggle" class="btn btn-primary">Hide Labels</button>
            <button onclick="toggleStats()" id="stats-toggle" class="btn btn-outline-secondary">Stats</button>
        </div>
        <div style="display: flex; align-items: center; gap: 15px;">
            <span><strong>Legend:</strong></span>
            <span style="display: flex; align-items: center; gap: 5px;">
                <span style="width: 15px; height: 15px; background: gold; clip-path: polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%);"></span> Hub
            </span>
            <span style="display: flex; align-items: center; gap: 5px;">
                <span style="width: 15px; height: 15px; background: #377eb8; transform: rotate(45deg);"></span> Bridge
            </span>
            <span style="display: flex; align-items: center; gap: 5px;">
                <span style="width: 15px; height: 15px; border-radius: 50%; background: #4daf4a;"></span> Standard
            </span>
        </div>
    </div>

    <div id="stats-container" style="display: none; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background: #f8f9fa;">
        <h5>Graph Statistics</h5>
        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
            <div><strong>Nodes:</strong> {num_nodes}</div>
            <div><strong>Edges:</strong> {num_edges}</div>
            <div><strong>Communities:</strong> {num_communities}</div>
            <div><strong>Hubs:</strong> {num_hubs}</div>
            <div><strong>Bridges:</strong> {num_bridges}</div>
        </div>
    </div>

    <div id="physics-settings-container" style="display: none; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
        <h5>Physics Settings</h5>
        <div style="display: flex; flex-wrap: wrap; gap: 15px;">
            <div>
                <label>Solver</label>
                <select id="physics-solver" class="form-select" onchange="changeSolver()">
                    <option value="forceAtlas2Based">Force Atlas 2</option>
                    <option value="barnesHut">Barnes-Hut</option>
                    <option value="repulsion">Repulsion</option>
                </select>
            </div>
            <div>
                <label>Gravity: <span id="grav-val">-50</span></label>
                <input type="range" id="gravity" min="-200" max="0" value="-50" oninput="document.getElementById('grav-val').innerText=this.value">
            </div>
            <div>
                <label>Spring Length: <span id="spring-val">100</span></label>
                <input type="range" id="spring" min="10" max="500" value="100" oninput="document.getElementById('spring-val').innerText=this.value">
            </div>
            <button onclick="applyPhysics()" class="btn btn-success">Apply</button>
        </div>
    </div>

    <div id="filter-container" style="display: none; margin: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
        <div style="display: flex; gap: 10px; align-items: center;">
            <select id="node-select" class="form-select" style="max-width: 300px;">
                <option value="">Select a Node...</option>
            </select>
            <button onclick="focusNode()" class="btn btn-primary">Focus</button>
            <button onclick="resetView()" class="btn btn-secondary">Reset View</button>
        </div>
    </div>

    <div id="mynetwork" class="card-body" style="flex: 1;"></div>

    <div id="footer" style="position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%); padding: 5px 10px; text-align: center; font-size: 0.85rem; background: rgba(255,255,255,0.8); border-radius: 4px;">
        <strong>{title}</strong> | Nodes: {num_nodes} | Edges: {num_edges} | Communities: {num_communities} | Hubs: {num_hubs} | Bridges: {num_bridges}
    </div>
</div>

<style>
html, body {{ height: 100%; margin: 0; padding: 0; overflow: hidden; }}
.card {{ border-radius: 0; margin: 0; }}
body.dark-mode {{ background: #121212; color: #e0e0e0; }}
body.dark-mode .card {{ background: #1e1e1e; }}
body.dark-mode #mynetwork {{ background: #000; }}
body.dark-mode #stats-container, body.dark-mode #physics-settings-container, body.dark-mode #filter-container {{ background: #2d2d2d; border-color: #444; }}
body.dark-mode .form-select {{ background: #333; color: #e0e0e0; border-color: #555; }}
body.dark-mode #footer {{ background: rgba(30,30,30,0.8); }}
.vis-network text {{ fill: #000 !important; }}
body.dark-mode .vis-network text {{ fill: #fff !important; }}
</style>

<script>
let labelsVisible = true;
let physicsEnabled = true;

function togglePhysics() {{
    const btn = document.getElementById('physics-toggle');
    physicsEnabled = !physicsEnabled;
    network.setOptions({{physics: {{enabled: physicsEnabled}}}});
    btn.textContent = physicsEnabled ? 'Disable Physics' : 'Enable Physics';
    btn.classList.toggle('btn-outline-primary', !physicsEnabled);
    btn.classList.toggle('btn-primary', physicsEnabled);
}}

function togglePhysicsSettings() {{
    const c = document.getElementById('physics-settings-container');
    const btn = document.getElementById('physics-settings-toggle');
    const show = c.style.display === 'none';
    c.style.display = show ? 'block' : 'none';
    btn.textContent = show ? 'Hide Settings' : 'Physics Settings';
    btn.classList.toggle('btn-info', show);
    btn.classList.toggle('btn-outline-info', !show);
}}

function stabilizeNetwork() {{ network.stabilize(100); }}

function toggleDarkMode() {{
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    document.getElementById('theme-toggle').textContent = isDark ? 'Light Mode' : 'Dark Mode';
    network.setOptions({{
        nodes: {{ font: {{ color: isDark ? '#fff' : '#000' }} }},
        edges: {{ font: {{ color: isDark ? '#ffdd00' : '#000' }} }}
    }});
}}

function toggleFilters() {{
    const c = document.getElementById('filter-container');
    const btn = document.getElementById('filter-toggle');
    const show = c.style.display === 'none';
    c.style.display = show ? 'block' : 'none';
    btn.textContent = show ? 'Hide Filters' : 'Show Filters';
    if (show) populateNodeSelect();
}}

function toggleLabels() {{
    labelsVisible = !labelsVisible;
    const btn = document.getElementById('labels-toggle');
    network.setOptions({{
        nodes: {{ font: {{ size: labelsVisible ? 12 : 0 }} }},
        edges: {{ font: {{ size: labelsVisible ? 10 : 0 }} }}
    }});
    btn.textContent = labelsVisible ? 'Hide Labels' : 'Show Labels';
}}

function toggleStats() {{
    const c = document.getElementById('stats-container');
    const btn = document.getElementById('stats-toggle');
    const show = c.style.display === 'none';
    c.style.display = show ? 'block' : 'none';
    btn.textContent = show ? 'Hide Stats' : 'Stats';
}}

function populateNodeSelect() {{
    const sel = document.getElementById('node-select');
    sel.innerHTML = '<option value="">Select a Node...</option>';
    network.body.data.nodes.getIds().sort().forEach(id => {{
        const opt = document.createElement('option');
        opt.value = id;
        opt.text = id;
        sel.appendChild(opt);
    }});
}}

function focusNode() {{
    const id = document.getElementById('node-select').value;
    if (id) {{
        network.selectNodes([id]);
        network.focus(id, {{ scale: 1.5, animation: true }});
    }}
}}

function resetView() {{
    network.unselectAll();
    network.fit();
}}

function changeSolver() {{
    const solver = document.getElementById('physics-solver').value;
    network.setOptions({{ physics: {{ solver: solver }} }});
}}

function applyPhysics() {{
    const solver = document.getElementById('physics-solver').value;
    const grav = parseFloat(document.getElementById('gravity').value);
    const spring = parseFloat(document.getElementById('spring').value);

    const opts = {{ physics: {{ solver: solver }} }};
    opts.physics[solver] = {{ gravitationalConstant: grav, springLength: spring }};
    network.setOptions(opts);
}}

network.once("stabilizationIterationsDone", function() {{
    network.fit();
}});

window.addEventListener('resize', () => network && network.fit());
</script>
'''

    # Replace the default div
    html = html.replace('<div id="mynetwork" class="card-body"></div>', custom_controls)

    # Remove default PyVis headers
    html = re.sub(r'<center>\s*<h1>.*?</h1>\s*</center>', '', html)
    html = html.replace('<h1></h1>', '')

    return html
