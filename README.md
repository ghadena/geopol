# GEOPOL: Knowledge Graph for Political Media Intelligence

GEOPOL is a data-driven application that combines Machine Learning Classification, large language models (LLMs), graph analytics, and web-based visualization to analyze and interpret election-related political news. The project extracts entities and sentiment from news articles, classifies articles by election relevance, and builds a dynamic knowledge graph that visually represents actors, topics, and relationships.

The main objective is to assist political campaign teams, analysts, and researchers in navigating complex media ecosystems by identifying key narratives and influential entities. The system supports exploratory analysis of political discourse in recent elections in the US, France, and Germany.

The workflow includes:
- **LLM-powered extraction** of named entities and sentiment from raw article text.
- **Machine learning classification** to detect election-relevant content.
- **Knowledge graph construction** using NetworkX and entity relationship modeling.
- **Interactive dashboard** built with Vis.js and Flask, enabling users to filter by sentiment and relationship typ, as well as explore centrality and graph structure.

The codebase is modular, with separate folders for data processing, modeling, visualization, and dashboard assets. The system is scalable and adaptable to new datasets and use cases.

This project was developed as a capstone for a Master’s program in Business Analytics and is designed to demonstrate both technical depth and real-world applicability.