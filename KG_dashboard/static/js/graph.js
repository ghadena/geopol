let network = null;

function clearSearch() {
    const search = document.getElementById('search').value.trim() || "";
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

function loadGraph() {
    const sentiment = document.getElementById('sentiment').value;
    const relationship = document.getElementById('relationship').value;
    const search = document.getElementById('search').value;
    const direction = document.getElementById('direction')?.value || 'all';
    const startDate = "";
    const endDate = "";

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
        if (!container) {
        console.error("❌ #network container not found.");
        return;
        }

        const options = {
        nodes: {
            shape: 'dot',
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
          size: Math.max(10, node.centrality * 300),
          title: `
            <strong>${node.label}</strong><br>
            Type: ${node.type}<br>
            Centrality: ${node.centrality}<br>
            Incoming: ${node.in_count}<br>
            Outgoing: ${node.out_count}
          `
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
            <strong>${edge.label}</strong><br>
            From: ${edge.from}<br>
            To: ${edge.to}<br>
            Sentiment: ${edge.sentiment}<br>
            Date: ${edge.date}<br>
            <a href="${edge.url}" target="_blank" style="text-decoration:none;color:blue;">🔗 Source</a>
          `
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
  // 🎚️ Date slider setup
  const minDate = new Date("2020-01-01");
  const maxDate = new Date("2025-12-31");

  loadGraph();
});
