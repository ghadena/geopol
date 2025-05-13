let network = null;

function getSentimentColor(sentiment) {
    const map = {
    FRIENDLY: 'green',
    HOSTILE: 'red',
    NEUTRAL: 'gray'
    };
    return map[sentiment] || 'black';
}

function loadGraph() {
    const sentiment = document.getElementById('sentiment').value;
    const relationship = document.getElementById('relationship').value;
    const search = document.getElementById('search').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const direction = document.getElementById('direction')?.value || 'all';

    const params = new URLSearchParams({
    sentiment, relationship, search,
    start_date: startDate,
    end_date: endDate,
    direction
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
                max: 50
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
        },
            interaction: {
            hover: true,
            tooltipDelay: 100
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
            nodeMap[node.id] = {
            id: node.id,
            label: node.label,
            group: node.group,
            size: Math.max(10, node.centrality * 300),
            title: `
                <div style="font-size:13px">
                <strong>${node.label}</strong><br>
                Type: ${node.type}<br>
                Centrality: ${node.centrality}<br>
                Incoming: ${node.in_count}<br>
                Outgoing: ${node.out_count}
                </div>
            `
            };
        });
        const dedupedNodes = Object.values(nodeMap);

        // Deduplicate and style edges
        const edgeMap = {};
        data.edges.forEach(edge => {
            const key = `${edge.from}->${edge.to}:${edge.label}`;
            edgeMap[key] = {
            from: edge.from,
            to: edge.to,
            label: edge.label,
            arrows: "to",
            color: getSentimentColor(edge.sentiment),
            title: `
                <div style="font-size:13px">
                <strong>${edge.label}</strong><br>
                From: ${edge.from}<br>
                To: ${edge.to}<br>
                Sentiment: ${edge.sentiment}<br>
                Date: ${edge.date}<br>
                Source: <a href="${edge.url}" target="_blank">${edge.url}</a>
                </div>
            `
            };
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

window.addEventListener("load", loadGraph);