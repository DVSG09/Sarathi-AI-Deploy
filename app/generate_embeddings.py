# generate_embeddings.py
import os
import sqlite3
import json
from dotenv import load_dotenv
import openai

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "sarathi-embedding")

if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_KEY:
    raise RuntimeError("❌ Missing Azure OpenAI credentials. Check your `.env` file.")

# Configure OpenAI client for Azure
openai.api_type = "azure"
openai.api_base = AZURE_OPENAI_ENDPOINT
openai.api_version = AZURE_OPENAI_API_VERSION
openai.api_key = AZURE_OPENAI_KEY

# -----------------------------
# Database setup
# -----------------------------
DB_FILE = "sarathi_feed.db"
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# -----------------------------
# Generate embeddings
# -----------------------------
def generate_embedding(text: str):
    response = openai.Embedding.create(
        input=text,
        engine=AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    )
    return response['data'][0]['embedding']

cursor.execute("SELECT id, content FROM feed_entries WHERE embedding IS NULL OR embedding = ''")
rows = cursor.fetchall()

print(f"Found {len(rows)} rows without embeddings.")

for row in rows:
    row_id, content = row
    if not content:
        continue

    try:
        embedding = generate_embedding(content[:2000])  # limit length
        cursor.execute(
            "UPDATE feed_entries SET embedding=? WHERE id=?",
            (json.dumps(embedding), row_id)
        )
        print(f"✅ Updated embedding for row {row_id}")
        conn.commit()
    except Exception as e:
        print(f"❌ Failed for row {row_id}: {e}")

conn.close()
print("🎉 All embeddings generated and saved.")
