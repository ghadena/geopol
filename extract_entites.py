# import os
# import re
# import json
# import time
# import pandas as pd
# from pyspark.sql import SparkSession
# from google.generativeai import GenerativeModel, configure
# from dotenv import load_dotenv
# from tqdm import tqdm
# import argparse

# # --- CONFIGURE ---
# load_dotenv()
# configure(api_key=os.environ["GOOGLE_API_KEY"])
# model = GenerativeModel("gemini-1.5-flash")

# # --- PARAMETERS ---
# parser = argparse.ArgumentParser()
# parser.add_argument("--source_table", type=str, required=True, help="Full path of the source Delta table")
# parser.add_argument("--output_table", type=str, required=True, help="Full path of the output Delta table")

# args = parser.parse_args()
# SOURCE_TABLE = args.source_table
# OUTPUT_TABLE = args.output_table

# TEXT_COLUMN = "text"
# ROW_ID_COLUMN = "url"
# BATCH_SIZE = 5
# SLEEP_BETWEEN_BATCHES = 1  # seconds

# # --- SPARK ---
# spark = SparkSession.builder.getOrCreate()

# # --- CLEAN JSON FUNCTION ---
# def clean_json_response(response_content):
#     match = re.search(r'\{[\s\S]*\}', response_content)
#     if match:
#         return match.group(0)
#     return None

# # --- PROMPT FUNCTION ---
# def build_prompt(text):
#     return f"""
# Extract named entities from the following text and classify them into categories:

# - people (individuals, only nominative case, no inflected forms)
# - institutions (organizations, government agencies, companies)
# - political_events (historical or ongoing political events)
# - political_parties (official political parties)
# - locations (cities, countries, regions)

# Also, extract the sentiment **between** entities. The sentiment between two entities (if present) should be labeled as one of: "FRIENDLY", "HOSTILE", or "NEUTRAL".

# Return the result in this JSON format:
# {{
#   "entities": {{
#     "people": [...],
#     "institutions": [...],
#     "political_events": [...],
#     "political_parties": [...],
#     "locations": [...]
#   }},
#   "entity_sentiment_edges": [
#     {{"source": "EntityA", "target": "EntityB", "sentiment": "HOSTILE"}},
#     ...
#   ]
# }}

# Text:
# {text}
# """

# # --- MAIN FUNCTION ---
# def main(source_table, output_table):
#     df = spark.read.table(SOURCE_TABLE).select(ROW_ID_COLUMN, TEXT_COLUMN).toPandas()

#     # Ensure output table exists (create with schema if needed)
#     if not spark._jsparkSession.catalog().tableExists(OUTPUT_TABLE):
#         spark.createDataFrame([], schema=f"{ROW_ID_COLUMN} string, extracted_entities string, entity_sentiment_edges string") \
#             .write.format("delta").saveAsTable(OUTPUT_TABLE)

#     for i in tqdm(range(len(df))):
#         row = df.iloc[i]
#         row_id = row[ROW_ID_COLUMN]
#         text = row[TEXT_COLUMN]

#         if not isinstance(text, str) or len(text.strip()) == 0:
#             continue  # skip empty

#         prompt = build_prompt(text)
#         try:
#             response = model.generate_content(prompt)
#             response_text = response.text.strip()

#             cleaned_json = clean_json_response(response_text)
#             if cleaned_json is None:
#                 raise ValueError("No valid JSON returned by model.")

#             parsed = json.loads(cleaned_json)
#             extracted_entities = json.dumps(parsed.get("entities", {}), ensure_ascii=False)
#             sentiment_edges = json.dumps(parsed.get("entity_sentiment_edges", []), ensure_ascii=False)

#         except Exception as e:
#             print(f"[ERROR] row {i} ({row_id}): {e}")
#             extracted_entities = json.dumps({})
#             sentiment_edges = json.dumps([])

#         # Write single row to output table
#         single_row_df = spark.createDataFrame(
#             [(row_id, extracted_entities, sentiment_edges)],
#             schema=f"{ROW_ID_COLUMN} string, extracted_entities string, entity_sentiment_edges string"
#         )

#         single_row_df.write.format("delta").mode("append").saveAsTable(OUTPUT_TABLE)
#         time.sleep(SLEEP_BETWEEN_BATCHES)

#     print(f"✅ Finished. Output written to: {OUTPUT_TABLE}")

# if __name__ == "__main__":
#     main()


import os
import re
import json
import time
import pandas as pd
from pyspark.sql import SparkSession
from google.generativeai import GenerativeModel, configure
from dotenv import load_dotenv
from tqdm import tqdm

# --- CONFIGURE GOOGLE GEMINI ---
load_dotenv()
configure(api_key=os.environ["GOOGLE_API_KEY"])
model = GenerativeModel("gemini-1.5-flash")

# --- SETTINGS ---
TEXT_COLUMN = "text"
ROW_ID_COLUMN = "url"
BATCH_SIZE = 5
SLEEP_BETWEEN_BATCHES = 1  # seconds

# --- SPARK SESSION ---
spark = SparkSession.builder.getOrCreate()

# --- CLEAN JSON FUNCTION ---
def clean_json_response(response_content):
    match = re.search(r'\{[\s\S]*\}', response_content)
    if match:
        return match.group(0)
    return None

# --- PROMPT GENERATOR ---
def build_prompt(text):
    return f"""
Extract named entities from the following text and classify them into categories:

- people (individuals, only nominative case, no inflected forms)
- institutions (organizations, government agencies, companies)
- political_events (historical or ongoing political events)
- political_parties (official political parties)
- locations (cities, countries, regions)

Also, extract the sentiment **between** entities. The sentiment between two entities (if present) should be labeled as one of: "FRIENDLY", "HOSTILE", or "NEUTRAL".

Return the result in this JSON format:
{{
  "entities": {{
    "people": [...],
    "institutions": [...],
    "political_events": [...],
    "political_parties": [...],
    "locations": [...]
  }},
  "entity_sentiment_edges": [
    {{"source": "EntityA", "target": "EntityB", "sentiment": "HOSTILE"}},
    ...
  ]
}}

Text:
{text}
"""

# --- MAIN PROCESSING FUNCTION ---
def main(source_table, output_table):
    df = spark.read.table(source_table).select(ROW_ID_COLUMN, TEXT_COLUMN).toPandas()

    # Ensure output table exists
    if not spark._jsparkSession.catalog().tableExists(output_table):
        spark.createDataFrame([], schema=f"{ROW_ID_COLUMN} string, extracted_entities string, entity_sentiment_edges string") \
            .write.format("delta").saveAsTable(output_table)

    for i in tqdm(range(len(df))):
        row = df.iloc[i]
        row_id = row[ROW_ID_COLUMN]
        text = row[TEXT_COLUMN]

        if not isinstance(text, str) or len(text.strip()) == 0:
            continue

        prompt = build_prompt(text)
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()

            cleaned_json = clean_json_response(response_text)
            if cleaned_json is None:
                raise ValueError("No valid JSON returned by model.")

            parsed = json.loads(cleaned_json)
            extracted_entities = json.dumps(parsed.get("entities", {}), ensure_ascii=False)
            sentiment_edges = json.dumps(parsed.get("entity_sentiment_edges", []), ensure_ascii=False)

        except Exception as e:
            print(f"[ERROR] row {i} ({row_id}): {e}")
            extracted_entities = json.dumps({})
            sentiment_edges = json.dumps([])

        # Save one row immediately
        single_row_df = spark.createDataFrame(
            [(row_id, extracted_entities, sentiment_edges)],
            schema=f"{ROW_ID_COLUMN} string, extracted_entities string, entity_sentiment_edges string"
        )
        single_row_df.write.format("delta").mode("append").saveAsTable(output_table)
        time.sleep(SLEEP_BETWEEN_BATCHES)

    print(f"✅ Done! Output saved to: {output_table}")