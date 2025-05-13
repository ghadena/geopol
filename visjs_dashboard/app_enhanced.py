
from flask import Flask, render_template, request, jsonify
import pandas as pd
import networkx as nx

app = Flask(__name__)

edges_df = pd.read_csv("edges.csv")
entities_df = pd.read_csv("entities.csv")

edges_df["source"] = edges_df["source"].str.strip()
edges_df["target"] = edges_df["target"].str.strip()
entities_df["entity"] = entities_df["entity"].str.strip()
entities_df["entity_type"] = entities_df["entity_type"].str.strip()
edges_df["date"] = edges_df["date"].astype(str)

@app.route("/")
def index():
    return render_template("index.html")

def safe_parse_date(val):
    try:
        val = float(val)
        return datetime.utcfromtimestamp(val / 1000).strftime("%Y-%m-%d")
    except:
        return val

@app.route("/data")
def data():
    sentiment = request.args.get("sentiment", "All")
    relationship = request.args.get("relationship", "All")
    search = request.args.get("search", "").lower()
    start_date = safe_parse_date(request.args.get("start_date"))
    end_date = safe_parse_date(request.args.get("end_date"))
    direction = request.args.get("direction", "all")

    df = edges_df.copy()

    if sentiment != "All":
        df = df[df["sentiment"] == sentiment]
    if relationship != "All":
        df = df[df["relationship"] == relationship]
    if start_date and end_date:
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    if search:
        if direction == "incoming":
            df = df[df["target"].str.lower().str.contains(search)]
        elif direction == "outgoing":
            df = df[df["source"].str.lower().str.contains(search)]
        else:
            df = df[df["source"].str.lower().str.contains(search) | df["target"].str.lower().str.contains(search)]

    G = nx.from_pandas_edgelist(df, "source", "target", create_using=nx.DiGraph())
    centrality = nx.degree_centrality(G)
    indeg = dict(G.in_degree())
    outdeg = dict(G.out_degree())

    nodes = set(df["source"]).union(set(df["target"]))
    node_data = entities_df[entities_df["entity"].isin(nodes)].drop_duplicates("entity")

    nodes_list = []
    for _, row in node_data.iterrows():
        node_id = row["entity"]
        nodes_list.append({
            "id": node_id,
            "label": node_id,
            "group": row["entity_type"],
            "type": row["entity_type"],
            "centrality": round(centrality.get(node_id, 0), 4),
            "in_count": indeg.get(node_id, 0),
            "out_count": outdeg.get(node_id, 0)
        })

    edges_list = []
    for _, row in df.iterrows():
        edges_list.append({
            "from": row["source"],
            "to": row["target"],
            "label": row["relationship"],
            "sentiment": row["sentiment"],
            "date": row["date"],
            "url": row.get("url", ""),
            "arrows": "to"
        })

    return jsonify({
        "nodes": nodes_list,
        "edges": edges_list,
        "relationship_types": sorted(edges_df["relationship"].dropna().unique().tolist())
    })

if __name__ == "__main__":
    app.run(debug=True)
