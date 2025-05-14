
from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

edges_df = pd.read_csv("edges.csv")
entities_df = pd.read_csv("entities.csv")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    sentiment = request.args.get("sentiment", "All")
    relationship = request.args.get("relationship", "All")
    search = request.args.get("search", "").lower()
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    df = edges_df.copy()

    if sentiment != "All":
        df = df[df["sentiment"] == sentiment]
    if relationship != "All":
        df = df[df["relationship"] == relationship]
    if start_date and end_date:
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    if search:
        df = df[df["source"].str.lower().str.contains(search) |
                df["target"].str.lower().str.contains(search)]

    nodes = set(df["source"]).union(set(df["target"]))
    node_data = entities_df[entities_df["entity"].isin(nodes)]

    nodes_list = []
    for _, row in node_data.iterrows():
        nodes_list.append({
            "id": row["entity"],
            "label": row["entity"],
            "group": row["entity_type"]
        })

    edges_list = []
    for _, row in df.iterrows():
        edges_list.append({
            "from": row["source"],
            "to": row["target"],
            "label": row["relationship"],
            "arrows": "to",
            "title": f"Sentiment: {row['sentiment']}<br>Date: {row['date']}<br>URL: {row['url']}"
        })

    return jsonify({"nodes": nodes_list, "edges": edges_list})

if __name__ == "__main__":
    app.run(debug=True)
