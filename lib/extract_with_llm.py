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
model = GenerativeModel("gemini-1.5-flash-8b")

# --- SETTINGS ---
TEXT_COLUMN = "article_text"
DESC_COLUMN = "description"
ROW_ID_COLUMN = "url"
LANG_COLUMN = "language"
SLEEP_BETWEEN_BATCHES = 1
BACKUP_EVERY = 200

MASTER_CSV = "gemini_results_master.csv"
ERROR_LOG_CSV = "gemini_errors.csv"
BACKUP_FOLDER = "backups"

# --- INITIALIZE SPARK ---
spark = SparkSession.builder.getOrCreate()

# --- CLEAN JSON RESPONSE ---
def clean_json_response(response_content):
    match = re.search(r'\{[\s\S]*\}', response_content)
    if match:
        return match.group(0)
    return None

# --- PROMPT FUNCTIONS ---
def build_prompt(text, lang):
    return f"""
This text is in: {lang}
Read and understand the following news article in its original language. Then, extract the following information and reply ONLY in English, in the exact JSON format below:

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

5. Indicate if the text is relevant to the German or French elections.

Reply ONLY in this exact JSON format, and in English:

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
  ],
  "relevant_to_german_or_french_elections": true
}}

Text:
{text}
"""

def main(source):
    print("📥 Loading data...")

    # Load data based on input type
    if isinstance(source, pd.DataFrame):
        df = source
    elif isinstance(source, str):
        if source.endswith('.csv'):
            df = pd.read_csv(source)
        elif source.endswith('.parquet'):
            df = pd.read_parquet(source)
        else:
            # Assume it's a Spark table name
            df = spark.read.table(source).toPandas()
    else:
        raise ValueError("Unsupported source type. Provide a DataFrame, CSV/Parquet file path, or Spark table name.")

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

    # --- Filter for allowed languages ---
    allowed_langs = ["en", "fr", "de"]
    if LANG_COLUMN in df.columns:
        df = df[df[LANG_COLUMN].isin(allowed_langs)]
    else:
        print("⚠️ No language column found. Skipping language filtering.")

    results = []
    full_results = []
    errors = []

    for i in tqdm(range(len(df))):
        row = df.iloc[i]
        row_id = row[ROW_ID_COLUMN]
        lang = row[LANG_COLUMN] if LANG_COLUMN in row else "en"
        text = row.get(TEXT_COLUMN, "")
        if not isinstance(text, str) or len(text.strip()) == 0:
            text = row.get(DESC_COLUMN, "")
        if not isinstance(text, str) or len(text.strip()) == 0:
            continue  # skip if both are empty
        text = text.strip()

        # Select prompt based on language
        prompt = build_prompt(text, lang)

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
        relevant_to_elections = None

        if response_text:
            try:
                cleaned_json = clean_json_response(response_text)
                if cleaned_json is None:
                    raise ValueError("No valid JSON returned by model.")
                parsed = json.loads(cleaned_json)
                extracted_entities = parsed.get("entities", {})
                relationships = parsed.get("entity_relationships", [])
                relevant_to_elections = parsed.get("relevant_to_german_or_french_elections", None)
            except Exception as parse_error:
                print(f"[JSON ERROR] row {i} ({row_id}): {parse_error}")
                errors.append({"url": row_id, "error": str(parse_error)})

        row_result = {
            "url": row_id,
            "lang": lang,
            "extracted_entities": extracted_entities,
            "entity_relationships": relationships,
            "relevant_to_german_or_french_elections": relevant_to_elections
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