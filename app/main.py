from fastapi import FastAPI, UploadFile, File, Form   # ✅ add Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import re
import sqlite3
from dotenv import load_dotenv
from openai import AzureOpenAI
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "sarathi-deploy")

if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_KEY:
    raise RuntimeError("❌ Missing Azure OpenAI credentials. Check your `.env` file.")

# -----------------------------
# Azure OpenAI client
# -----------------------------
client = AzureOpenAI(
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY
)

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.mount("/static", StaticFiles(directory="static"), name="static")

# -----------------------------
# Database setup
# -----------------------------
DB_FILE = "sarathi_feed.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feed_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_type TEXT DEFAULT 'file',
            source TEXT,
            title TEXT DEFAULT 'MyPursu Info',
            tags TEXT DEFAULT '',
            content TEXT,
            metadata TEXT DEFAULT '{}',
            status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# Predefined MyPursu website
# -----------------------------
MY_PURSU_URL = "https://mypursu.com/"

def crawl_mypursu_website():
    try:
        response = requests.get(MY_PURSU_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator="\n")
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO feed_entries 
            (entry_type, source, title, tags, content, metadata, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "WEB",
                MY_PURSU_URL,
                "MyPursu Website",
                "mypursu,website",
                text[:4000],
                json.dumps({"source_type": "web", "added_by": "crawler"}),
                "active",
                now,
                now
            )
        )
        conn.commit()
        conn.close()
        logging.info("✅ MyPursu website content added to feed DB")
    except Exception as e:
        logging.error(f"Error crawling website: {e}")

crawl_mypursu_website()

# -----------------------------
# Request models
# -----------------------------
class ChatRequest(BaseModel):
    message: str

class ServiceRequest(BaseModel):
    service: str

# -----------------------------
# Serve index.html
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "env": {
            "endpoint": AZURE_OPENAI_ENDPOINT,
            "deployment": AZURE_OPENAI_DEPLOYMENT,
            "api_version": AZURE_OPENAI_API_VERSION,
        }
    }

# -----------------------------
# Feed helpers
# -----------------------------
STOPWORDS = {"the","and","for","with","this","that","have","from","your","you","are",
             "was","were","will","what","when","how","why","can","could","should",
             "about","on","in","to","of","it","is","as","at","by","or","an","a"}

def _clean_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()

def fetch_db_context(user_message: str, max_entries: int = 5) -> str:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    qwords = {w for w in re.findall(r"[A-Za-z0-9]{3,}", user_message.lower())}
    scored = []

    try:
        cursor.execute("SELECT id, entry_type, source, title, tags, content FROM feed_entries")
        rows = cursor.fetchall()
        for row in rows:
            content = (row[5] or "").strip()
            if not content:
                continue
            score = sum(content.lower().count(w) for w in qwords) + 0.1
            scored.append((score, row[2], content))
    except Exception as e:
        logging.error(f"DB fetch error: {e}")
    finally:
        conn.close()

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = []
    total_chars = 0
    for score, source, content in scored[:max_entries]:
        snippet = content[:800]
        add = f"[Source: {source}] {snippet}"
        if total_chars + len(add) > 4000:
            break
        selected.append(add)
        total_chars += len(add)

    return "\n\n".join(selected)

def build_feed_context(user_message: str, max_chars: int = 4000, k: int = 5) -> str:
    qwords = {w for w in re.findall(r"[A-Za-z0-9]{3,}", (user_message or "").lower()) if w not in STOPWORDS}
    scored = []
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, entry_type, source, title, tags, content FROM feed_entries ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        text = _clean_text(row[5])[:2000]
        if not text:
            continue
        lw = text.lower()
        score = sum(lw.count(w) for w in qwords) + 0.1
        scored.append((score, row[2], text))

    scored.sort(key=lambda x: x[0], reverse=True)
    chunks, total = [], 0
    for score, source, text in scored:
        snippet = text[:800]
        add = f"[Source: {source}] {snippet}"
        if total + len(add) > max_chars:
            break
        chunks.append(add)
        total += len(add)
        if len(chunks) >= k:
            break
    return "\n\n".join(chunks)

# -----------------------------
# Dummy agent logic
# -----------------------------
def get_enhanced_response(user_id: str, text: str, enabled_intents: set):
    text_lower = text.lower()
    intent = "faq"
    escalated = False
    tool_calls = []
    metadata = {}
    reply_text = "✅ You selected the service." if text_lower in [s.lower() for s in enabled_intents] else ""
    return reply_text, tool_calls, escalated, intent, metadata

# -----------------------------
# ChatGPT restricted to MyPursu
# -----------------------------
def generate_chatgpt_response(user_message: str, context: str) -> str:
    try:
        prompt = f"""
You are Sarathi AI, a MyPursu assistant. Only answer questions about MyPursu services, guides, or features. 
Do NOT answer unrelated questions. If unrelated, reply: "I can only answer questions about MyPursu services."
Use the following context: {context}

User asked: "{user_message}"
Provide a concise, user-friendly answer.
"""
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=300
        )
        final_reply = response.choices[0].message.content

        now = datetime.utcnow().isoformat()
        # Save Q&A in DB with proper defaults
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO feed_entries 
            (entry_type, source, title, tags, content, metadata, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "QA",
                "ChatGPT",
                "MyPursu Q&A",
                "mypursu,qa",
                f"Q: {user_message}\nA: {final_reply}"[:4000],
                json.dumps({"source_type": "chat", "added_by": "chatgpt"}),
                "active",
                now,
                now
            )
        )
        conn.commit()
        conn.close()

        return final_reply
    except Exception as e:
        logging.error(f"ChatGPT error: {e}")
        return "Oops! I couldn't generate a response. Please try again."

# -----------------------------
# Chat endpoint
# -----------------------------
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_message = (request.message or "").strip()
    if not user_message:
        return {"response": "Please enter a message.", "intent": "none"}

    db_context = fetch_db_context(user_message)
    feed_context = build_feed_context(user_message)

    reply_text, tool_calls, escalated, intent, metadata = get_enhanced_response(
        user_id="user_default",
        text=user_message,
        enabled_intents={"Scan & Pay","Pay to UPI","Pay to Static QR","Concierge Package",
                         "Bill Payments","Travel Bookings","Mail Box","Pack N Ship","Withdraw",
                         "History","Remit2Any"}
    )

    combined_context = ""
    if db_context:
        combined_context += f"{db_context}\n\n"
    if feed_context:
        combined_context += f"{feed_context}\n\n"
    if reply_text:
        combined_context += reply_text

    if intent in {"faq", "chatgpt"} or escalated:
        final_reply = generate_chatgpt_response(user_message, combined_context)
    else:
        final_reply = reply_text

    return {
        "response": final_reply,
        "intent": intent,
        "tool_calls": tool_calls,
        "escalated": escalated,
        "metadata": metadata
    }

# -----------------------------
# Service endpoint
# -----------------------------
@app.post("/service")
async def service_endpoint(request: ServiceRequest):
    service = (request.service or "").strip()
    if not service:
        return {"response": "Please select a service."}

    db_context = fetch_db_context(service)
    feed_context = build_feed_context(service)

    combined_context = ""
    if db_context:
        combined_context += f"{db_context}\n\n"
    if feed_context:
        combined_context += f"{feed_context}\n\n"

    final_reply = generate_chatgpt_response(f"Tell me about the {service} service.", combined_context)

    return {
        "response": final_reply,
        "intent": "service_info",
        "tool_calls": [],
        "escalated": False,
        "metadata": {}
    }

# -----------------------------
# Feed endpoints
# -----------------------------
@app.get("/feed")
async def get_feed():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, entry_type, source, title, tags, content FROM feed_entries ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    feed = [{"id": r[0], "type": r[1], "source": r[2], "title": r[3], "tags": r[4], "preview": r[5][:150]} for r in rows]
    return feed

@app.put("/feed/edit")
async def edit_feed(entry: dict):
    id = entry.get("id")
    new_content = entry.get("new_content")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE feed_entries SET content=?, updated_at=? WHERE id=?", (new_content, datetime.utcnow().isoformat(), id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/feed/delete/{id}")
async def delete_feed(id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM feed_entries WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

# -----------------------------
# ✅ Support endpoint (NEW)
# -----------------------------
@app.post("/support")
async def support_request(
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    now = datetime.utcnow().isoformat()

    # Save request into DB (optional: create new table if needed)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT,
            created_at TEXT
        )
    """)
    cursor.execute(
        "INSERT INTO support_requests (name, email, message, created_at) VALUES (?, ?, ?, ?)",
        (name, email, message, now)
    )
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": f"✅ Thanks {name}, our live agent team will reach out to you at {email}."
    }
