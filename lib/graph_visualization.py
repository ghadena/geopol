import pandas as pd
import networkx as nx
from pyvis.network import Network
from community import community_louvain
import os
import webbrowser
from flask import Flask, request, jsonify
import threading
import time

app = Flask(__name__)

# Color mappings
type_colors = {
    "people": "#ffd700",  # yellow
    "organizations": "#ff7f0e",  # orange
    "locations": "#9467bd",  # purple
    "political_events": "#7f7f7f",  # gray
    "political_parties": "#2ca02c",  # green
    "institutions": "#1f77b4",  # blue
    "unknown": "#d62728",  # red
}

sentiment_colors = {
    "FRIENDLY": "green",
    "HOSTILE": "red",
    "NEUTRAL": "gray"
}

# Global variables to store data
edges_df = None
ents_long = None

def generate_graph(sentiment="All", relationship="All", date_range_values=None, search_term=""):
    """
    Generate an interactive knowledge graph visualization.
    """
    global edges_df, ents_long
    
    # Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    filtered_edges = edges_df.copy()
    
    # Apply filters
    if sentiment != "All":
        filtered_edges = filtered_edges[filtered_edges["sentiment"] == sentiment]
    if relationship != "All":
        filtered_edges = filtered_edges[filtered_edges["relationship"] == relationship]
    if date_range_values:
        filtered_edges = filtered_edges[
            (filtered_edges["date"] >= date_range_values[0]) &
            (filtered_edges["date"] <= date_range_values[1])
        ]

    # Create directed graph
    G = nx.DiGraph()
    for _, row in filtered_edges.iterrows():
        G.add_edge(row['source'], row['target'], 
                   sentiment=row['sentiment'], 
                   relationship=row['relationship'], 
                   url=row['url'], 
                   date=str(row['date']))

    # If search term exists, filter to only show connected nodes
    if search_term:
        connected_nodes = set()
        for node in G.nodes():
            if search_term.lower() in node.lower():
                connected_nodes.add(node)
                connected_nodes.update(G.neighbors(node))
                connected_nodes.update(G.predecessors(node))
        G = G.subgraph(connected_nodes).copy()

    # Calculate centralities
    in_deg_cent = nx.in_degree_centrality(G)
    out_deg_cent = nx.out_degree_centrality(G)
    deg_cent = nx.degree_centrality(G)
    
    # Get top nodes by degree centrality
    top_nodes = sorted(deg_cent.items(), key=lambda x: x[1], reverse=True)[:20]
    top_node_ids = [node for node, _ in top_nodes]

    # Detect communities
    partition = community_louvain.best_partition(G.to_undirected())
    
    # Create entity type mapping
    entity_type_map = ents_long.drop_duplicates('entity').set_index('entity')['entity_type'].to_dict()
    
    # Create the network
    net = Network(
        height="750px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
        notebook=True,
        cdn_resources='in_line',
        directed=True
    )

    # Enhanced physics options
    net.set_options("""
    {
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -100,
                "centralGravity": 0.01,
                "springLength": 200,
                "springConstant": 0.08,
                "damping": 0.4,
                "avoidOverlap": 1
            },
            "maxVelocity": 10,
            "minVelocity": 0.1,
            "solver": "forceAtlas2Based",
            "stabilization": {
                "enabled": true,
                "iterations": 2000,
                "updateInterval": 50,
                "onlyDynamicEdges": false,
                "fit": true
            }
        },
        "edges": {
            "smooth": {
                "enabled": true,
                "type": "continuous",
                "forceDirection": "none",
                "roundness": 0.5
            },
            "color": {
                "inherit": true
            },
            "width": 1,
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 1.5,
                    "type": "arrow"
                }
            }
        },
        "nodes": {
            "font": {
                "size": 14,
                "face": "arial"
            },
            "scaling": {
                "min": 10,
                "max": 30
            }
        }
    }
    """)

    # Add nodes
    for node in G.nodes():
        entity_type = entity_type_map.get(node, "unknown")
        color = type_colors.get(entity_type, "#d3d3d3")
        size = 10 + deg_cent.get(node, 0) * 100
        
        # Show label for searched node, top nodes, or when zoomed in
        label = node if (node in top_node_ids or 
                        (search_term and search_term.lower() in node.lower())) else ""
        
        # Highlight searched node
        if search_term and search_term.lower() in node.lower():
            color = "#ff0000"
            size *= 1.5
        
        hover_text = f"""
        <div style='font-size: 14px;'>
            <b>{node}</b> ({entity_type})<br>
            Community: {partition.get(node, 0)}<br>
            Incoming relationships: {in_deg_cent.get(node, 0):.2f}<br>
            Outgoing relationships: {out_deg_cent.get(node, 0):.2f}<br>
            Total relationships: {deg_cent.get(node, 0):.2f}
        </div>
        """
        
        net.add_node(
            n_id=node, 
            label=label,
            title=hover_text,
            color=color, 
            size=size,
            group=partition.get(node, 0)
        )

    # Add edges
    for u, v, d in G.edges(data=True):
        color = sentiment_colors.get(d.get('sentiment', "NEUTRAL"), "gray")
        label = d.get('relationship', '')
        title = f"""
        <div style='font-size: 14px;'>
            <b>From:</b> {u}<br>
            <b>To:</b> {v}<br>
            <b>Relationship:</b> {label}<br>
            <b>Sentiment:</b> {d.get('sentiment')}<br>
            <b>Date:</b> {d.get('date')}
        </div>
        """
        net.add_edge(
            u, v, 
            color=color, 
            title=title, 
            value=1,
            smooth=True,
            width=1
        )

    # Add custom HTML with filters and controls
    custom_html = """
    <div style="position: absolute; top: 10px; right: 10px; z-index: 1000; background: rgba(255,255,255,0.9); padding: 10px; border-radius: 5px;">
        <div style="margin-bottom: 10px;">
            <input type="text" id="searchInput" placeholder="Search nodes..." 
                   style="padding: 5px; border-radius: 4px; border: 1px solid #ccc; width: 200px;">
            <button onclick="searchNodes()" 
                    style="padding: 5px 10px; border-radius: 4px; border: 1px solid #ccc; background: #fff;">
                Search
            </button>
        </div>
        <div style="margin-bottom: 10px;">
            <select id="sentimentFilter" onchange="applyFilters()" 
                    style="padding: 5px; border-radius: 4px; border: 1px solid #ccc; width: 200px;">
                <option value="All">All Sentiments</option>
                <option value="FRIENDLY">Friendly</option>
                <option value="HOSTILE">Hostile</option>
                <option value="NEUTRAL">Neutral</option>
            </select>
        </div>
        <div style="margin-bottom: 10px;">
            <select id="relationshipFilter" onchange="applyFilters()" 
                    style="padding: 5px; border-radius: 4px; border: 1px solid #ccc; width: 200px;">
                <option value="All">All Relationships</option>
                <option value="SUPPORTS">Supports</option>
                <option value="OPPOSES">Opposes</option>
                <option value="WORKS_WITH">Works With</option>
            </select>
        </div>
        <div style="margin-bottom: 10px;">
            <label>Date Range:</label><br>
            <input type="date" id="startDate" style="width: 95px; margin-right: 5px;">
            <input type="date" id="endDate" style="width: 95px;">
        </div>
        <div style="margin-bottom: 10px;">
            <button onclick="applyFilters()" 
                    style="padding: 5px 10px; border-radius: 4px; border: 1px solid #ccc; background: #fff;">
                Apply Filters
            </button>
            <button onclick="togglePhysics()" 
                    style="padding: 5px 10px; border-radius: 4px; border: 1px solid #ccc; background: #fff;">
                Toggle Physics
            </button>
            <button onclick="resetView()" 
                    style="padding: 5px 10px; border-radius: 4px; border: 1px solid #ccc; background: #fff;">
                Reset View
            </button>
        </div>
    </div>
    <script>
    function searchNodes() {
        var searchTerm = document.getElementById('searchInput').value.toLowerCase();
        applyFilters(searchTerm);
    }

    function applyFilters(searchTerm) {
        var sentiment = document.getElementById('sentimentFilter').value;
        var relationship = document.getElementById('relationshipFilter').value;
        var startDate = document.getElementById('startDate').value;
        var endDate = document.getElementById('endDate').value;
        
        fetch('/update_graph', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sentiment: sentiment,
                relationship: relationship,
                startDate: startDate,
                endDate: endDate,
                searchTerm: searchTerm || document.getElementById('searchInput').value.toLowerCase()
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            }
        });
    }
    
    function togglePhysics() {
        var physics = network.getOptions().physics;
        network.setOptions({ physics: { enabled: !physics.enabled } });
    }

    function resetView() {
        network.fit({
            animation: {
                duration: 1000,
                easingFunction: 'easeInOutQuad'
            }
        });
    }

    network.on("zoom", function() {
        var zoom = network.getScale();
        var nodes = network.body.data.nodes;
        nodes.forEach(function(node) {
            if (zoom > 1.5) {
                node.label = node.id;
            } else {
                node.label = node.id in topNodes ? node.id : "";
            }
        });
        network.body.data.nodes.update(nodes);
    });
    </script>
    """
    
    # Save and display
    output_file = os.path.join(output_dir, 'filtered_kg.html')
    net.save_graph(output_file)
    
    with open(output_file, 'r') as f:
        content = f.read()
    
    content = content.replace('</body>', f'{custom_html}</body>')
    
    with open(output_file, 'w') as f:
        f.write(content)
    
    return output_file

@app.route('/')
def index():
    return app.send_static_file('filtered_kg.html')

@app.route('/update_graph', methods=['POST'])
def update_graph():
    data = request.json
    sentiment = data.get('sentiment', 'All')
    relationship = data.get('relationship', 'All')
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    search_term = data.get('searchTerm', '')
    
    date_range = None
    if start_date and end_date:
        date_range = (start_date, end_date)
    
    generate_graph(sentiment, relationship, date_range, search_term)
    return jsonify({'success': True})

def start_server():
    app.run(port=5000)

if __name__ == "__main__":
    # Load data
    edges_df = pd.read_csv('edges.csv')
    ents_long = pd.read_csv('entities.csv')
    
    # Generate initial graph
    output_file = generate_graph()
    
    # Start Flask server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait for server to start
    time.sleep(1)
    
    # Open browser
    webbrowser.open('http://localhost:5000')