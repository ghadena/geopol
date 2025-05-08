# # import os
# # import re
# # import json
# # import time
# # import pandas as pd
# # from pyspark.sql import SparkSession
# # from google.generativeai import GenerativeModel, configure
# # from dotenv import load_dotenv
# # from tqdm import tqdm

# # # --- CONFIGURE GOOGLE API ---
# # load_dotenv()
# # configure(api_key=os.environ["GOOGLE_API_KEY"])
# # model = GenerativeModel("gemini-1.5-flash")

# # # --- SETTINGS ---
# # TEXT_COLUMN = "text"
# # ROW_ID_COLUMN = "url"
# # SLEEP_BETWEEN_BATCHES = 1  # seconds between each request

# # # --- INITIALIZE SPARK ---
# # spark = SparkSession.builder.getOrCreate()

# # # --- CLEAN JSON RESPONSE ---
# # def clean_json_response(response_content):
# #     match = re.search(r'\{[\s\S]*\}', response_content)
# #     if match:
# #         return match.group(0)
# #     return None

# # # --- GEMINI PROMPT ---
# # def build_prompt(text):
# #     return f"""
# # Extract named entities from the following text and classify them into categories:

# # - people (individuals, only nominative case, no inflected forms)
# # - institutions (organizations, government agencies, companies)
# # - political_events (historical or ongoing political events)
# # - political_parties (official political parties)
# # - locations (cities, countries, regions)

# # Also, extract the sentiment **between** entities. The sentiment between two entities (if present) should be labeled as one of: "FRIENDLY", "HOSTILE", or "NEUTRAL".

# # Return the result in this JSON format:
# # {{
# #   "entities": {{
# #     "people": [...],
# #     "institutions": [...],
# #     "political_events": [...],
# #     "political_parties": [...],
# #     "locations": [...]
# #   }},
# #   "entity_sentiment_edges": [
# #     {{"source": "EntityA", "target": "EntityB", "sentiment": "HOSTILE"}},
# #     ...
# #   ]
# # }}

# # Text:
# # {text}
# # """

# # # --- MAIN FUNCTION ---
# # def main(source_table):
# #     # df = spark.read.table(source_table).select(ROW_ID_COLUMN, TEXT_COLUMN).toPandas()
# #     df = spark.read.table(source_table).select(ROW_ID_COLUMN, TEXT_COLUMN).limit(10).toPandas()
# #     results = []

# #     try:
# #         for i in tqdm(range(len(df))):
# #             row = df.iloc[i]
# #             row_id = row[ROW_ID_COLUMN]
# #             text = row[TEXT_COLUMN]

# #             if not isinstance(text, str) or len(text.strip()) == 0:
# #                 continue

# #             prompt = build_prompt(text)

# #             try:
# #                 response = model.generate_content(prompt)
# #                 response_text = response.text.strip()
# #                 cleaned_json = clean_json_response(response_text)

# #                 if cleaned_json is None:
# #                     raise ValueError("No valid JSON returned by model.")

# #                 parsed = json.loads(cleaned_json)
# #                 extracted_entities = parsed.get("entities", {})
# #                 sentiment_edges = parsed.get("entity_sentiment_edges", [])

# #             except Exception as e:
# #                 if "429" in str(e) and "retry_delay" in str(e):
# #                     print(f"[RATE LIMIT] row {i} ({row_id}): {e}")
# #                     # Extract delay seconds if mentioned
# #                     delay_match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)', str(e))
# #                     delay_seconds = int(delay_match.group(1)) if delay_match else 60
# #                     print(f"⏳ Waiting {delay_seconds} seconds before retrying...")

# #                     time.sleep(delay_seconds)
# #                     try:
# #                         response = model.generate_content(prompt)
# #                         response_text = response.text.strip()
# #                         cleaned_json = clean_json_response(response_text)
# #                         parsed = json.loads(cleaned_json)
# #                         extracted_entities = parsed.get("entities", {})
# #                         sentiment_edges = parsed.get("entity_sentiment_edges", [])
# #                     except Exception as retry_error:
# #                         print(f"[FINAL FAIL] row {i} ({row_id}): {retry_error}")
# #                         extracted_entities = {}
# #                         sentiment_edges = []
# #                 else:
# #                     print(f"[ERROR] row {i} ({row_id}): {e}")
# #                     extracted_entities = {}
# #                     sentiment_edges = []

# #             results.append({
# #                 "url": row_id,
# #                 "extracted_entities": extracted_entities,
# #                 "entity_sentiment_edges": sentiment_edges
# #             })

# #             time.sleep(SLEEP_BETWEEN_BATCHES)

# #     except Exception as outer_error:
# #         print(f"❌ Script interrupted: {outer_error}")
# #         print("⚠️ Returning partial results collected so far.")

# #     result_df = pd.DataFrame(results)
# #     print(f"✅ Done. Extracted {len(result_df)} rows.")
# #     return result_df

# import os
# import re
# import json
# import time
# import pandas as pd
# from pyspark.sql import SparkSession
# from google.generativeai import GenerativeModel, configure
# from dotenv import load_dotenv
# from tqdm import tqdm

# # --- CONFIGURE GOOGLE API ---
# load_dotenv()
# configure(api_key=os.environ["GOOGLE_API_KEY"])
# model = GenerativeModel("gemini-1.5-flash")

# # --- SETTINGS ---
# TEXT_COLUMN = "text"
# ROW_ID_COLUMN = "url"
# SLEEP_BETWEEN_BATCHES = 1  # seconds
# BACKUP_PATH = "gemini_partial_results.json"

# # --- INITIALIZE SPARK ---
# spark = SparkSession.builder.getOrCreate()

# # --- CLEAN JSON RESPONSE ---
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
# def main(source_table):
#     df = spark.read.table(source_table).select(ROW_ID_COLUMN, TEXT_COLUMN).toPandas().head(10)
#     results = []

#     for i in tqdm(range(len(df))):
#         row = df.iloc[i]
#         row_id = row[ROW_ID_COLUMN]
#         text = row[TEXT_COLUMN]

#         if not isinstance(text, str) or len(text.strip()) == 0:
#             continue

#         prompt = build_prompt(text)

#         try:
#             response = model.generate_content(prompt)
#             response_text = response.text.strip()
#             cleaned_json = clean_json_response(response_text)

#             if cleaned_json is None:
#                 raise ValueError("No valid JSON returned by model.")

#             parsed = json.loads(cleaned_json)
#             extracted_entities = parsed.get("entities", {})
#             sentiment_edges = parsed.get("entity_sentiment_edges", [])

#         except Exception as e:
#             if "429" in str(e) and "retry_delay" in str(e):
#                 print(f"[RATE LIMIT] row {i} ({row_id}): {e}")
#                 delay_match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)', str(e))
#                 delay_seconds = int(delay_match.group(1)) if delay_match else 60
#                 print(f"⏳ Waiting {delay_seconds} seconds before retrying...")
#                 time.sleep(delay_seconds)

#                 try:
#                     response = model.generate_content(prompt)
#                     response_text = response.text.strip()
#                     cleaned_json = clean_json_response(response_text)
#                     parsed = json.loads(cleaned_json)
#                     extracted_entities = parsed.get("entities", {})
#                     sentiment_edges = parsed.get("entity_sentiment_edges", [])
#                 except Exception as retry_error:
#                     print(f"[FINAL FAIL] row {i} ({row_id}): {retry_error}")
#                     extracted_entities = {}
#                     sentiment_edges = []
#             else:
#                 print(f"[ERROR] row {i} ({row_id}): {e}")
#                 extracted_entities = {}
#                 sentiment_edges = []

#         results.append({
#             "url": row_id,
#             "extracted_entities": extracted_entities,
#             "entity_sentiment_edges": sentiment_edges
#         })

#         # ✅ Save backup after each row
#         pd.DataFrame(results).to_json(BACKUP_PATH, orient="records", lines=True)
#         time.sleep(SLEEP_BETWEEN_BATCHES)

#     result_df = pd.DataFrame(results)
#     print(f"✅ Done. Extracted {len(result_df)} rows.")
#     return result_df


import os
import re
import json
import time
import pandas as pd
from pyspark.sql import SparkSession
from google.generativeai import GenerativeModel, configure
from dotenv import load_dotenv
from tqdm import tqdm
from datetime import datetime

# --- CONFIGURE GOOGLE API ---
load_dotenv()
configure(api_key=os.environ["GOOGLE_API_KEY"])
model = GenerativeModel("gemini-2.0-flash-lite")

# --- SETTINGS ---
TEXT_COLUMN = "text"
ROW_ID_COLUMN = "url"
SLEEP_BETWEEN_BATCHES = 1
BACKUP_EVERY = 200

MASTER_CSV = "gemini_results_master2.csv"
ERROR_LOG_CSV = "gemini_errors2.csv"
BACKUP_FOLDER = "backups2"


# --- INITIALIZE SPARK ---
spark = SparkSession.builder.getOrCreate()

# --- CLEAN JSON RESPONSE ---
def clean_json_response(response_content):
    match = re.search(r'\{[\s\S]*\}', response_content)
    if match:
        return match.group(0)
    return None

# --- PROMPT FUNCTION ---
def build_prompt(text):
    return f"""
Extract named entities and relationships from the following news article. Follow these instructions carefully:

1. Extract named entities and classify them into the following categories:
   - people (individuals, nominative form only)
   - institutions (organizations, government agencies, companies)
   - political_events (elections, debates, protests)
   - political_parties (official political parties)
   - locations (countries, cities, regions)

2. Identify any meaningful relationships between the entities.
   Use only these types: "supports", "criticizes", "endorses", "opposes", "represents", "leads", "partners with", "accuses"

3. For each relationship, if any sentiment is expressed, include it as: "FRIENDLY", "HOSTILE", or "NEUTRAL"

4. If no entities or relationships are found, return this structure with empty lists.

Return your output in **this exact JSON format**:

{{
  "entities": {{
    "people": [],
    "institutions": [],
    "political_events": [],
    "political_parties": [],
    "locations": []
  }},
  "entity_relationships": [
    {{
      "source": "EntityA",
      "target": "EntityB",
      "relationship": "supports",
      "sentiment": "FRIENDLY"
    }}
  ]
}}

Text:
{text}
"""

# --- MAIN FUNCTION ---
def main(source_table):
    print("📥 Loading table...")
    df = spark.read.table(source_table).select(ROW_ID_COLUMN, TEXT_COLUMN).toPandas()

    # --- Ensure the backups directory exists ---
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)
        print(f"📁 Created backup folder: {BACKUP_FOLDER}")
    else:
        print(f"📁 Backup folder already exists: {BACKUP_FOLDER}")

    # --- Resume logic ---
    if os.path.exists(MASTER_CSV):
        completed_df = pd.read_csv(MASTER_CSV)
        completed_urls = set(completed_df[ROW_ID_COLUMN])
        df = df[~df[ROW_ID_COLUMN].isin(completed_urls)]
        print(f"🔁 Resuming. Skipping {len(completed_urls)} already-processed rows.")
    else:
        completed_urls = set()

    results = []
    full_results = []
    errors = []

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
        except Exception as e:
            if "rate limit" in str(e).lower() or "quota" in str(e).lower() or "429" in str(e):
                print(f"[RATE LIMIT] row {i} ({row_id}): {e}")
                wait_time = 60
                print(f"⏳ Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
                try:
                    response = model.generate_content(prompt)
                    response_text = response.text.strip()
                except Exception as retry_error:
                    print(f"[FINAL FAIL] row {i} ({row_id}): {retry_error}")
                    errors.append({"url": row_id, "error": str(retry_error)})
                    response_text = None
            else:
                print(f"[ERROR] row {i} ({row_id}): {e}")
                errors.append({"url": row_id, "error": str(e)})
                response_text = None

        extracted_entities = {}
        relationships = []

        if response_text:
            try:
                cleaned_json = clean_json_response(response_text)
                if cleaned_json is None:
                    raise ValueError("No valid JSON returned by model.")
                parsed = json.loads(cleaned_json)
                extracted_entities = parsed.get("entities", {})
                relationships = parsed.get("entity_relationships", [])
            except Exception as parse_error:
                print(f"[JSON ERROR] row {i} ({row_id}): {parse_error}")
                errors.append({"url": row_id, "error": str(parse_error)})

        row_result = {
            "url": row_id,
            "extracted_entities": extracted_entities,
            "entity_relationships": relationships
        }

        results.append(row_result)
        full_results.append(row_result)

        # --- Periodic backup ---
        if (i + 1) % BACKUP_EVERY == 0:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            backup_path = os.path.join(BACKUP_FOLDER, f"gemini_results_backup_{timestamp}.csv")
            pd.DataFrame(results).to_csv(backup_path, index=False)
            print(f"💾 Saved backup to {backup_path}")

            pd.DataFrame(results).to_csv(
                MASTER_CSV, mode='a', index=False, header=not os.path.exists(MASTER_CSV)
            )
            results = []

            if errors:
                pd.DataFrame(errors).to_csv(
                    ERROR_LOG_CSV, mode='a', index=False, header=not os.path.exists(ERROR_LOG_CSV)
                )
                errors = []

        time.sleep(SLEEP_BETWEEN_BATCHES)

    # --- Final write for any remaining results not yet saved ---
    if results:
        pd.DataFrame(results).to_csv(
            MASTER_CSV, mode='a', index=False, header=not os.path.exists(MASTER_CSV)
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        backup_path = os.path.join(BACKUP_FOLDER, f"gemini_results_backup_{timestamp}_final.csv")
        pd.DataFrame(results).to_csv(backup_path, index=False)
        print(f"💾 Final results saved to {backup_path}")

    if errors:
        pd.DataFrame(errors).to_csv(
            ERROR_LOG_CSV, mode='a', index=False, header=not os.path.exists(ERROR_LOG_CSV)
        )

    print(f"✅ Finished all rows. Returning {len(full_results)} results as DataFrame.")
    return pd.DataFrame(full_results)