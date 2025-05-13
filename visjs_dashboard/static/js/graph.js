
let network = null;

function loadGraph() {
    const sentiment = document.getElementById('sentiment').value;
    const relationship = document.getElementById('relationship').value;
    const search = document.getElementById('search').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    const params = new URLSearchParams({
        sentiment: sentiment,
        relationship: relationship,
        search: search,
        start_date: startDate,
        end_date: endDate
    });

    fetch(`/data?${params}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('network');

            const options = {
                nodes: {
                    shape: 'dot',
                    scaling: {
                        min: 10,
                        max: 30
                    },
                    font: {
                        size: 12,
                        face: 'arial'
                    }
                },
                edges: {
                    width: 1,
                    smooth: {
                        type: 'dynamic',
                        roundness: 0.6
                    }
                },
                physics: {
                    stabilization: false,
                    barnesHut: {
                        gravitationalConstant: -80000,
                        springConstant: 0.001,
                        springLength: 200
                    }
                }
            };

            if (network !== null) {
                network.destroy();
                network = null;
            }
            container.innerHTML = "";

            // Deduplicate nodes
            const nodeMap = {};
            data.nodes.forEach(node => {
                nodeMap[node.id] = node;  // Last wins
            });
            const dedupedNodes = Object.values(nodeMap);
            console.log("📦 Unique node count:", dedupedNodes.length);
            console.log("🧠 Node IDs:", dedupedNodes.map(n => n.id));

            // Deduplicate edges
            const edgeMap = {};
            data.edges.forEach(edge => {
                const key = `${edge.from}->${edge.to}:${edge.label}`;
                edgeMap[key] = edge;
            });
            const dedupedEdges = Object.values(edgeMap);

            const visData = {
                nodes: new vis.DataSet(dedupedNodes),
                edges: new vis.DataSet(dedupedEdges)
            };

            try {
                network = new vis.Network(container, visData, options);
                console.log('✅ Network created successfully');
            } catch (err) {
                console.error('❌ Error creating network:', err);
                alert('Error creating network: ' + err.message);
            }
        })
        .catch(error => {
            console.error('❌ Error fetching or rendering graph data:', error);
            alert('Error loading graph data: ' + error.message);
        });
}

function resetView() {
    if (network !== null) {
        network.fit();
    }
}

document.addEventListener('DOMContentLoaded', loadGraph);
