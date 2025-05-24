
# from flask import Flask, render_template, request, jsonify
# import pandas as pd
# import networkx as nx
# import google.generativeai as genai
# import os
# from dotenv import load_dotenv
# from pathlib import Path


# genai.configure(api_key="AIzaSyBEHPnDqF4nlQ8BlXJEo2LrAs9V5Sq7KIw")

# app = Flask(__name__)

# edges_df = pd.read_csv("https://raw.githubusercontent.com/ghadena/geopol/refs/heads/main/data/processed/edges.csv")
# entities_df = pd.read_csv("https://raw.githubusercontent.com/ghadena/geopol/refs/heads/main/data/processed/entities.csv")

# edges_df["source"] = edges_df["source"].str.strip()
# edges_df["target"] = edges_df["target"].str.strip()
# entities_df["entity"] = entities_df["entity"].str.strip()
# entities_df["entity_type"] = entities_df["entity_type"].str.strip()
# edges_df["date"] = edges_df["date"].astype(str)

# @app.route("/")
# def index():
#     return render_template("index.html")

# def safe_parse_date(val):
#     try:
#         val = float(val)
#         return datetime.utcfromtimestamp(val / 1000).strftime("%Y-%m-%d")
#     except:
#         return val

# @app.route("/data")
# def data():
#     sentiment = request.args.get("sentiment", "All")
#     relationship = request.args.get("relationship", "All")
#     search = request.args.get("search", "").lower()
#     start_date = safe_parse_date(request.args.get("start_date"))
#     end_date = safe_parse_date(request.args.get("end_date"))
#     direction = request.args.get("direction", "all")

#     df = edges_df.copy()

#     if sentiment != "All":
#         df = df[df["sentiment"] == sentiment]
#     if relationship != "All":
#         df = df[df["relationship"] == relationship]
#     if start_date and end_date:
#         df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

#     if search:
#         if direction == "incoming":
#             df = df[df["target"].str.lower().str.contains(search)]
#         elif direction == "outgoing":
#             df = df[df["source"].str.lower().str.contains(search)]
#         else:
#             df = df[df["source"].str.lower().str.contains(search) | df["target"].str.lower().str.contains(search)]

#     G = nx.from_pandas_edgelist(df, "source", "target", create_using=nx.DiGraph())
#     centrality = nx.degree_centrality(G)
#     indeg = dict(G.in_degree())
#     outdeg = dict(G.out_degree())

#     nodes = set(df["source"]).union(set(df["target"]))
#     node_data = entities_df[entities_df["entity"].isin(nodes)].drop_duplicates("entity")

#     nodes_list = []
#     for _, row in node_data.iterrows():
#         node_id = row["entity"]
#         nodes_list.append({
#             "id": node_id,
#             "label": node_id,
#             "group": row["entity_type"],
#             "type": row["entity_type"],
#             "centrality": round(centrality.get(node_id, 0), 4),
#             "in_count": indeg.get(node_id, 0),
#             "out_count": outdeg.get(node_id, 0)
#         })

#     edges_list = []
#     for _, row in df.iterrows():
#         edges_list.append({
#             "from": row["source"],
#             "to": row["target"],
#             "label": row["relationship"],
#             "sentiment": row["sentiment"],
#             "date": row["date"],
#             "url": row.get("url", ""),
#             "arrows": "to"
#         })

#     return jsonify({
#         "nodes": nodes_list,
#         "edges": edges_list,
#         "relationship_types": sorted(edges_df["relationship"].dropna().unique().tolist()),
#         "min_date": df["date"].min(),
#         "max_date": df["date"].max()
#     })

# # @app.route("/ask", methods=["POST"])
# # # def ask():
# # #     question = request.json.get("question", "")
# # #     if not question:
# # #         return jsonify({"answer": "No question received."})

# # #     # Minimal Gemini example (replace with your key and model)
# # #     model = genai.GenerativeModel("gemini-pro")

# # #     # Use knowledge from edges (simple example context)
# # #     context = ""
# # #     for _, row in edges_df.iterrows():
# # #         context += f"{row['source']} {row['relationship']} {row['target']}. "

# # #     prompt = f"Context: {context}\nQuestion: {question}\nAnswer:"

# # #     try:
# # #         response = model.generate_content(prompt)
# # #         return jsonify({"answer": response.text})
# # #     except Exception as e:
# # #         return jsonify({"answer": f"Error: {str(e)}"})

# # @app.route("/ask", methods=["POST"])
# # def ask():
# #     print("✅ Received /ask request")
# #     question = request.json.get("question", "")
# #     return jsonify({"answer": f"You asked: {question}"})

# if __name__ == "__main__":
#     app.run(port=5757, debug=True)



# from flask import Flask, render_template, request, jsonify
# import pandas as pd
# import networkx as nx
# from datetime import datetime

# app = Flask(__name__)

# edges_df = pd.read_csv("/Users/ghadena/Desktop/geopol/notebooks/edges_new_filtered.csv")
# entities_df = pd.read_csv("/Users/ghadena/Desktop/geopol/notebooks/ents_long.csv")
# # Strip whitespace and ensure types
# edges_df["source"] = edges_df["source"].str.strip()
# edges_df["target"] = edges_df["target"].str.strip()
# edges_df["url"] = edges_df["url"].str.strip()
# edges_df["article_source"] = edges_df["article_source"].str.strip()
# edges_df["date"] = pd.to_datetime(edges_df["date"], errors="coerce").astype(str)

# entities_df["entity"] = entities_df["entity"].str.strip()
# entities_df["entity_type"] = entities_df["entity_type"].str.strip()
# entities_df["article_source"] = entities_df["article_source"].str.strip()

# @app.route("/")
# def index():
#     return render_template("index.html")

# def safe_parse_date(val):
#     try:
#         val = float(val)
#         return datetime.utcfromtimestamp(val / 1000).strftime("%Y-%m-%d")
#     except:
#         return val

# @app.route("/data")
# def data():
#     sentiment = request.args.get("sentiment", "All")
#     relationship = request.args.get("relationship", "All")
#     search = request.args.get("search", "").lower()
#     start_date = safe_parse_date(request.args.get("start_date"))
#     end_date = safe_parse_date(request.args.get("end_date"))
#     direction = request.args.get("direction", "all")
#     article_sources = request.args.getlist("article_sources")
    
#     df = edges_df.copy()
    
#     if article_sources:
#         df = df[df["article_source"].isin(article_sources)]
    

#     if sentiment != "All":
#         df = df[df["sentiment"] == sentiment]
#     if relationship != "All":
#         df = df[df["relationship"] == relationship]
#     if start_date and end_date:
#         df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
#     if election_sources:
#         df = df[df["article_source"].isin(election_sources)]

#     if search:
#         if direction == "incoming":
#             df = df[df["target"].str.lower().str.contains(search)]
#         elif direction == "outgoing":
#             df = df[df["source"].str.lower().str.contains(search)]
#         else:
#             df = df[df["source"].str.lower().str.contains(search) | df["target"].str.lower().str.contains(search)]

#     nodes = set(df["source"]).union(set(df["target"]))
#     node_data = entities_df[entities_df["entity"].isin(nodes)].drop_duplicates("entity")

#     centrality = nx.degree_centrality(nx.from_pandas_edgelist(df, "source", "target", create_using=nx.DiGraph()))
#     indeg = df.groupby("target").size().to_dict()
#     outdeg = df.groupby("source").size().to_dict()

#     shape_map = {
#         "US": "circle",
#         "French": "triangle",
#         "German": "square"
#     }

#     nodes_list = []
#     for _, row in node_data.iterrows():
#         article_source = row.get("article_source", "Other")
#         shape = shape_map.get(article_source, "dot")
#         node_id = row["entity"]
#         nodes_list.append({
#             "id": node_id,
#             "label": node_id,
#             "group": row["entity_type"],
#             "type": row["entity_type"],
#             "centrality": round(centrality.get(node_id, 0), 4),
#             "in_count": indeg.get(node_id, 0),
#             "out_count": outdeg.get(node_id, 0),
#             "shape": shape
#         })

#     edges_list = []
#     for _, row in df.iterrows():
#         edges_list.append({
#             "from": row["source"],
#             "to": row["target"],
#             "label": row["relationship"],
#             "sentiment": row["sentiment"],
#             "date": row["date"],
#             "url": row["url"],
#             "arrows": "to"
#         })

#     return jsonify({
#         "nodes": nodes_list,
#         "edges": edges_list,
#         "relationship_types": sorted(edges_df["relationship"].dropna().unique().tolist()),
#         "min_date": edges_df["date"].min(),
#         "max_date": edges_df["date"].max()
#     })

# if __name__ == "__main__":
#     app.run(port=5757, debug=True)
# from flask import Flask, render_template, request, jsonify
# import pandas as pd
# import networkx as nx
# from datetime import datetime

# app = Flask(__name__)

# # Load data
# edges_df = pd.read_csv("/Users/ghadena/Desktop/geopol/notebooks/edges_new_filtered.csv")
# entities_df = pd.read_csv("/Users/ghadena/Desktop/geopol/notebooks/ents_long.csv")

# # Clean up whitespace and types
# for col in ["source", "target", "url", "relationship", "sentiment", "article_source", "date"]:
#     if col in edges_df.columns:
#         edges_df[col] = edges_df[col].astype(str).str.strip()
# if "entity" in entities_df.columns:
#     entities_df["entity"] = entities_df["entity"].astype(str).str.strip()
# if "entity_type" in entities_df.columns:
#     entities_df["entity_type"] = entities_df["entity_type"].astype(str).str.strip()
# if "article_source" in entities_df.columns:
#     entities_df["article_source"] = entities_df["article_source"].str.lower().str.strip()

# # Helper to safely parse dates from JS timestamp or direct string

# def safe_parse_date(val):
#     try:
#         val = float(val)
#         return datetime.utcfromtimestamp(val / 1000).strftime("%Y-%m-%d")
#     except:
#         return val

# @app.route("/")
# def index():
#     return render_template("index.html")

# @app.route("/data")
# def data():
#     sentiment = request.args.get("sentiment", "All")
#     relationship = request.args.get("relationship", "All")
#     search = request.args.get("search", "").lower()
#     start_date = safe_parse_date(request.args.get("start_date"))
#     end_date = safe_parse_date(request.args.get("end_date"))
#     direction = request.args.get("direction", "all")
#     source_filters = request.args.getlist("article_source")

#     df = edges_df.copy()

#     # Filter by article source if selected
#     if source_filters:
#         df = df[df["article_source"].isin(source_filters)]

#     # Sentiment, relationship, date, search filters
#     if sentiment != "All":
#         df = df[df["sentiment"] == sentiment]
#     if relationship != "All":
#         df = df[df["relationship"] == relationship]
#     if start_date and end_date:
#         df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
#     if search:
#         if direction == "incoming":
#             df = df[df["target"].str.lower().str.contains(search)]
#         elif direction == "outgoing":
#             df = df[df["source"].str.lower().str.contains(search)]
#         else:
#             df = df[df["source"].str.lower().str.contains(search) | df["target"].str.lower().str.contains(search)]

#     # Build graph
#     G = nx.from_pandas_edgelist(df, "source", "target", create_using=nx.DiGraph())
#     centrality = nx.degree_centrality(G)
#     indeg = dict(G.in_degree())
#     outdeg = dict(G.out_degree())

#     nodes = set(df["source"]).union(set(df["target"]))
#     node_data = entities_df[entities_df["entity"].isin(nodes)].drop_duplicates("entity")

#     nodes_list = []
#     for _, row in node_data.iterrows():
#         article_source = row.get("article_source", "unknown")
#         shape = {
#             "us": "circle",
#             "french": "triangle",
#             "german": "square"
#         }.get(article_source, "dot")
#         nodes_list.append({
#             "id": row["entity"],
#             "label": row["entity"],
#             "group": row["entity_type"],
#             "type": row["entity_type"],
#             "centrality": round(centrality.get(row["entity"], 0), 4),
#             "in_count": indeg.get(row["entity"], 0),
#             "out_count": outdeg.get(row["entity"], 0),
#             "shape": shape
#         })

#     edges_list = []
#     for _, row in df.iterrows():
#         edges_list.append({
#             "from": row["source"],
#             "to": row["target"],
#             "label": row["relationship"],
#             "sentiment": row["sentiment"],
#             "date": row["date"],
#             "url": row.get("url", ""),
#             "arrows": "to"
#         })

#     return jsonify({
#         "nodes": nodes_list,
#         "edges": edges_list,
#         "relationship_types": sorted(edges_df["relationship"].dropna().unique().tolist()),
#         "article_sources": sorted(edges_df["article_source"].dropna().unique().tolist()),
#         "min_date": df["date"].min(),
#         "max_date": df["date"].max()
#     })

# if __name__ == "__main__":
#     app.run(port=5757, debug=True)

from flask import Flask, render_template, request, jsonify
import pandas as pd
import networkx as nx
import os
from datetime import datetime

app = Flask(__name__)

# Load preprocessed edges and entities
edges_df = pd.read_csv("/Users/ghadena/Desktop/geopol/notebooks/edges_new_filtered.csv")
entities_df = pd.read_csv("/Users/ghadena/Desktop/geopol/notebooks/ents_long.csv")

# Clean up whitespace and types
edges_df["source"] = edges_df["source"].astype(str).str.strip()
edges_df["target"] = edges_df["target"].astype(str).str.strip()
edges_df["article_source"] = edges_df["article_source"].astype(str).str.lower()
edges_df["date"] = edges_df["date"].astype(str)
entities_df["entity"] = entities_df["entity"].astype(str).str.strip()
entities_df["entity_type"] = entities_df["entity_type"].astype(str).str.strip()
entities_df["article_source"] = entities_df["article_source"].astype(str).str.lower()

@app.route("/")
def select_map():
    return render_template("select_map.html")

@app.route("/map/<source>")
def map_by_source(source):
    return render_template("index.html", source=source)

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
    article_source = request.args.get("article_source", "us").lower()

    df = edges_df[edges_df["article_source"].str.lower() == article_source].copy()
    
    if article_source:
        df = df[df["article_source"] == article_source.lower()]

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

    shape_map = {
        "us": "circle",
        "french": "triangle",
        "german": "square"
    }

    nodes_list = []
    for _, row in node_data.iterrows():
        src = row.get("article_source", "")
        shape = shape_map.get(src.lower(), "dot")
        nodes_list.append({
            "id": row["entity"],
            "label": row["entity"],
            "group": row["entity_type"],
            "type": row["entity_type"],
            "shape": shape,
            "centrality": round(centrality.get(row["entity"], 0), 4),
            "in_count": indeg.get(row["entity"], 0),
            "out_count": outdeg.get(row["entity"], 0)
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
        "relationship_types": sorted(edges_df["relationship"].dropna().unique().tolist()),
        "min_date": df["date"].min(),
        "max_date": df["date"].max()
    })

if __name__ == "__main__":
    app.run(port=5757, debug=True)
