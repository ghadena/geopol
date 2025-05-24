let network = null;

function clearSearch() {
    const input = document.getElementById('search');
    if (input) {
        input.value = "";
    }
    loadGraph();
}

function getSentimentColor(sentiment) {
    const map = {
        FRIENDLY: 'green',
        HOSTILE: 'red',
        NEUTRAL: 'gray'
    };
    return map[sentiment] || 'black';
}

function getSourceShape(source) {
  const map = {
    US: "circle",
    French: "triangle",
    German: "square"
  };
  return map[source] || "dot";
}

function loadGraph() {
    const articleSource = document.getElementById("articleSourceSelect").value;
    const sentiment = document.getElementById('sentiment').value;
    const relationship = document.getElementById('relationship').value;
    const search = document.getElementById('search').value;
    const direction = document.getElementById('direction')?.value || 'all';
    const startDate = document.getElementById('dateFrom').value;
    const endDate = document.getElementById('dateTo').value;
    
    const params = new URLSearchParams({
        sentiment,
        relationship,
        search,
        direction,
        start_date: startDate,
        end_date: endDate,
        article_source: articleSource
    });
    
//selectedSources.forEach(src => params.append("article_sources", src));
    
    fetch(`/data?${params}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('network');
            if (!container) {
                console.error("❌ #network container not found.");
                return;
            }

            const options = {
                nodes: {
                    scaling: { min: 10, max: 50 },
                    font: { size: 12, face: 'arial' }
                },
                edges: {
                    width: 1,
                    smooth: { type: 'dynamic', roundness: 0.6 }
                },
                physics: {
                    stabilization: false,
                    barnesHut: {
                        gravitationalConstant: -30000,
                        springLength: 150,
                        springConstant: 0.002,
                        damping: 0.5,
                    }
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 100
                }
            };

            const relationshipSelect = document.getElementById('relationship');
            if (relationshipSelect && data.relationship_types && Array.isArray(data.relationship_types)) {
                const current = relationshipSelect.value;
                relationshipSelect.innerHTML = '<option value="All">All</option>';
                data.relationship_types.forEach(r => {
                    const opt = document.createElement("option");
                    opt.value = r;
                    opt.textContent = r;
                    relationshipSelect.appendChild(opt);
                });
                relationshipSelect.value = current;
            }

            if (network !== null) {
                network.destroy();
                network = null;
            }
            container.innerHTML = "";

            const nodeMap = {};
            data.nodes.forEach(node => {
                nodeMap[node.id] = {
                    id: node.id,
                    label: node.label,
                    group: node.group,
                    shape:getSourceShape(node.source),
                    color: node.color || '#97C2FC',
                    size: Math.max(10, node.centrality * 300),
                    title: `
                        ${node.label}
                        Type: ${node.type}
                        Source: ${node.source}
                        Centrality: ${node.centrality}
                        Incoming: ${node.in_count}
                        Outgoing: ${node.out_count}`
                };
            });

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
                        ${edge.label}
                        From: ${edge.from}
                        To: ${edge.to}
                        Sentiment: ${edge.sentiment}
                        Date: ${edge.date}
                        <a href="${edge.url}" target="_blank" style="text-decoration:none;color:blue;">🔗 Source</a>`
                };
            });

            const visData = {
                nodes: new vis.DataSet(Object.values(nodeMap)),
                edges: new vis.DataSet(Object.values(edgeMap))
            };

            try {
                network = new vis.Network(container, visData, options);
                console.log("✅ Graph rendered.");
            } catch (err) {
                console.error("❌ Error rendering graph:", err);
                alert("Error creating graph: " + err.message);
            }
        })
        .catch(error => {
            console.error("❌ Fetch error:", error);
            alert("Error loading graph: " + error.message);
        });
}

function resetView() {
    if (network !== null) {
        network.fit();
    }
}

window.addEventListener("load", () => {
    loadGraph();
});