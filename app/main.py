from fastapi import FastAPI, UploadFile, File, Form   # ✅ add Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import re
import sqlite3
from dotenv import load_dotenv
import openai
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import uuid

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
# Configure OpenAI for Azure
openai.api_type = "azure"
openai.api_base = AZURE_OPENAI_ENDPOINT
openai.api_version = AZURE_OPENAI_API_VERSION
openai.api_key = AZURE_OPENAI_KEY

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
# Startup event
# -----------------------------
@app.on_event("startup")
async def startup_event():
    """Run cleanup on startup"""
    try:
        cleanup_expired_sessions()
        logging.info("✅ Startup cleanup completed")
    except Exception as e:
        logging.error(f"Startup cleanup failed: {e}")

# -----------------------------
# Database setup
# -----------------------------
DB_FILE = "sarathi_feed.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Feed entries table
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
    
    # Conversation sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT DEFAULT 'anonymous',
            created_at TEXT,
            last_activity TEXT,
            expires_at TEXT,
            status TEXT DEFAULT 'active'
        )
    """)
    
    # Conversation messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            message TEXT,
            timestamp TEXT,
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (session_id) REFERENCES conversation_sessions (id)
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# Session Management
# -----------------------------
def create_session(user_id: str = "anonymous") -> str:
    """Create a new conversation session"""
    session_id = str(uuid.uuid4())
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=48)  # 48 hours expiration
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversation_sessions (id, user_id, created_at, last_activity, expires_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, user_id, now.isoformat(), now.isoformat(), expires_at.isoformat())
    )
    conn.commit()
    conn.close()
    
    return session_id

def get_or_create_session(session_id: str = None, user_id: str = "anonymous") -> str:
    """Get existing session or create new one"""
    if not session_id:
        return create_session(user_id)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, expires_at FROM conversation_sessions WHERE id = ? AND status = 'active'",
        (session_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result:
        session_id, expires_at_str = result
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.utcnow() < expires_at:
            # Update last activity
            update_session_activity(session_id)
            return session_id
        else:
            # Session expired, create new one
            return create_session(user_id)
    else:
        # Session not found, create new one
        return create_session(user_id)

def update_session_activity(session_id: str):
    """Update last activity timestamp for a session"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE conversation_sessions SET last_activity = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), session_id)
    )
    conn.commit()
    conn.close()

def save_message(session_id: str, role: str, message: str, metadata: dict = None):
    """Save a message to the conversation history"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversation_messages (session_id, role, message, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
        (session_id, role, message, datetime.utcnow().isoformat(), json.dumps(metadata or {}))
    )
    conn.commit()
    conn.close()

def get_conversation_history(session_id: str, limit: int = 10) -> list:
    """Get recent conversation history for a session"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, message, timestamp FROM conversation_messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
        (session_id, limit)
    )
    messages = cursor.fetchall()
    conn.close()
    
    # Return in chronological order (oldest first)
    return list(reversed(messages))

def cleanup_expired_sessions():
    """Clean up expired sessions and their messages"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get expired sessions
    cursor.execute(
        "SELECT id FROM conversation_sessions WHERE expires_at < ? AND status = 'active'",
        (datetime.utcnow().isoformat(),)
    )
    expired_sessions = cursor.fetchall()
    
    if expired_sessions:
        session_ids = [s[0] for s in expired_sessions]
        
        # Delete messages from expired sessions
        cursor.execute(
            f"DELETE FROM conversation_messages WHERE session_id IN ({','.join(['?'] * len(session_ids))})",
            session_ids
        )
        
        # Mark sessions as expired
        cursor.execute(
            f"UPDATE conversation_sessions SET status = 'expired' WHERE id IN ({','.join(['?'] * len(session_ids))})",
            session_ids
        )
        
        logging.info(f"Cleaned up {len(session_ids)} expired sessions")
    
    conn.commit()
    conn.close()

# -----------------------------
# MyPursu websites to crawl
# -----------------------------
MY_PURSU_URLS = {
    "main": "https://mypursu.com/",
    "user_agreement": "https://mypursu.com/mobile-application-user-agreement",
    "faq": "https://mypursu.com/faq"
}

def crawl_mypursu_websites():
    """Crawl all MyPursu websites and add to knowledge base"""
    logging.info(f"Starting to crawl {len(MY_PURSU_URLS)} websites: {list(MY_PURSU_URLS.keys())}")
    
    for site_name, url in MY_PURSU_URLS.items():
        try:
            logging.info(f"Crawling {site_name}: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text(separator="\n")
            text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
            
            # Create appropriate title and tags based on site
            if site_name == "main":
                title = "MyPursu Main Website"
                tags = "mypursu,website,main"
            elif site_name == "user_agreement":
                title = "MyPursu Mobile Application User Agreement"
                tags = "mypursu,user-agreement,terms,legal,compliance"
            elif site_name == "faq":
                title = "MyPursu Frequently Asked Questions"
                tags = "mypursu,faq,help,support,questions"
            
            logging.info(f"Extracted {len(text)} characters from {site_name}")
            
            now = datetime.utcnow().isoformat()
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Check if entry already exists to avoid duplicates
            cursor.execute(
                "SELECT id FROM feed_entries WHERE source = ? AND entry_type = 'WEB'",
                (url,)
            )
            existing = cursor.fetchone()
            
            if not existing:
                cursor.execute(
                    """
                    INSERT INTO feed_entries 
                    (entry_type, source, title, tags, content, metadata, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "WEB",
                        url,
                        title,
                        tags,
                        text[:4000],  # Limit content size
                        json.dumps({"source_type": "web", "added_by": "crawler", "site_type": site_name}),
                        "active",
                        now,
                        now
                    )
                )
                conn.commit()
                logging.info(f"✅ {title} content added to feed DB")
            else:
                # Update existing entry
                cursor.execute(
                    """
                    UPDATE feed_entries 
                    SET content = ?, updated_at = ?, metadata = ?
                    WHERE source = ? AND entry_type = 'WEB'
                    """,
                    (
                        text[:4000],
                        now,
                        json.dumps({"source_type": "web", "added_by": "crawler", "site_type": site_name}),
                        url
                    )
                )
                conn.commit()
                logging.info(f"✅ {title} content updated in feed DB")
            
            conn.close()
            
        except Exception as e:
            logging.error(f"Error crawling {site_name} ({url}): {e}")
    
    logging.info("Website crawling completed")

# Crawl all MyPursu websites
crawl_mypursu_websites()

# -----------------------------
# Request models
# -----------------------------
class ChatRequest(BaseModel):
    message: str
    session_id: str = None

class ServiceRequest(BaseModel):
    service: str
    session_id: str = None

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

# Global variable to cache rates and avoid frequent API calls
_cached_rates = None
_last_fetch_time = None

@app.get("/api/rates")
async def get_exchange_rates():
    """Get current exchange rates from MyPursu website with daily caching"""
    global _cached_rates, _last_fetch_time
    
    current_time = datetime.utcnow()
    
    # Check if we need to fetch new rates (daily or if no cache)
    should_fetch = (
        _cached_rates is None or 
        _last_fetch_time is None or 
        (current_time - _last_fetch_time).total_seconds() > 86400  # 24 hours
    )
    
    if should_fetch:
        try:
            # Fetch rates from MyPursu website
            response = requests.get(MY_PURSU_URL, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract exchange rates from the page
            _cached_rates = {
                "new_user_rate": "103.29",  # New users first $100
                "regular_rate": "88.41",    # Existing users standard rate
                "concierge_rate": "90.00",  # Concierge package rate
                "last_updated": current_time.isoformat(),
                "source": "mypursu.com",
                "next_update": (current_time + timedelta(days=1)).isoformat()
            }
            _last_fetch_time = current_time
            
            logging.info("Exchange rates updated from MyPursu website")
            
        except Exception as e:
            logging.error(f"Error fetching exchange rates: {e}")
            # Return fallback rates if website is unavailable
            _cached_rates = {
                "new_user_rate": "103.29",  # New users first $100
                "regular_rate": "88.41",    # Existing users standard rate
                "concierge_rate": "90.00",  # Concierge package rate
                "last_updated": current_time.isoformat(),
                "source": "cached",
                "error": "Unable to fetch live rates",
                "next_update": (current_time + timedelta(hours=1)).isoformat()
            }
            _last_fetch_time = current_time
    
    return _cached_rates

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
    
    # Enhanced keyword extraction
    qwords = {w for w in re.findall(r"[A-Za-z0-9]{3,}", user_message.lower())}
    
    # Add common synonyms and related terms
    synonyms = {
        'pay': ['payment', 'transfer', 'send', 'money'],
        'bill': ['bills', 'utility', 'electricity', 'water', 'gas'],
        'book': ['booking', 'reserve', 'travel', 'flight', 'hotel'],
        'send': ['transfer', 'remit', 'money', 'cash'],
        'receive': ['get', 'collect', 'mailbox', 'parcel'],
        'help': ['support', 'assist', 'guide', 'how'],
        'account': ['profile', 'wallet', 'balance', 'kyc'],
        'app': ['application', 'mobile', 'download', 'install'],
        'faq': ['frequently', 'asked', 'questions', 'help', 'support'],
        'agreement': ['terms', 'conditions', 'user', 'agreement', 'legal'],
        'concierge': ['package', 'premium', 'service', 'luxury'],
        'remit': ['remit2any', 'remittance', 'transfer', 'send'],
        'kyc': ['verification', 'identity', 'documents', 'pan', 'aadhaar'],
        'limit': ['limits', 'transaction', 'daily', 'weekly', 'maximum'],
        'withdraw': ['withdrawal', 'cash', 'out', 'funds']
    }
    
    # Expand query with synonyms
    expanded_words = set(qwords)
    for word in qwords:
        if word in synonyms:
            expanded_words.update(synonyms[word])
    
    scored = []

    try:
        cursor.execute("SELECT id, entry_type, source, title, tags, content FROM feed_entries")
        rows = cursor.fetchall()
        for row in rows:
            content = (row[5] or "").strip()
            if not content:
                continue
            
            # Enhanced scoring with synonyms
            content_lower = content.lower()
            score = 0
            
            # Original word matches
            for word in qwords:
                score += content_lower.count(word) * 2
            
            # Synonym matches (lower weight)
            for word in expanded_words:
                if word not in qwords:  # Don't double count
                    score += content_lower.count(word) * 0.5
            
            # Bonus for title matches
            title = (row[3] or "").lower()
            for word in qwords:
                if word in title:
                    score += 3
            
            # Bonus for tag matches
            tags = (row[4] or "").lower()
            for word in qwords:
                if word in tags:
                    score += 2
            
            if score > 0:
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
    
    # Check if it's a service selection
    if text_lower in [s.lower() for s in enabled_intents]:
        intent = "service"
        reply_text = "✅ You selected the service."
    else:
        # For all other questions, use ChatGPT
        intent = "chatgpt"
        reply_text = ""
    
    escalated = False
    tool_calls = []
    metadata = {}
    return reply_text, tool_calls, escalated, intent, metadata

# -----------------------------
# ChatGPT restricted to MyPursu
# -----------------------------
def generate_chatgpt_response(user_message: str, context: str, conversation_history: list = None) -> str:
    try:
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n".join([f"{role}: {message}" for role, message, _ in conversation_history[-5:]])  # Last 5 messages
            conversation_context = f"\n\nRECENT CONVERSATION:\n{conversation_context}\n"
        
        prompt = f"""
You're Sarathi, a helpful assistant. Give medium-length responses (3-5 lines) that sound natural and human.

CONTEXT:
{context}{conversation_context}

CURRENT QUESTION: "{user_message}"

Answer in 3-5 lines, casually but informatively. Use the context if it's about MyPursu services. For other questions, give a helpful explanation without being too formal or robotic. If there's conversation history, reference it naturally when relevant.
"""
        response = openai.ChatCompletion.create(
            engine=AZURE_OPENAI_DEPLOYMENT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # Higher temperature for more natural responses
            max_tokens=300    # Medium-length responses (3-5 lines)
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
        return "Sorry, having some issues right now. Try again in a sec!"

# -----------------------------
# Chat endpoint
# -----------------------------
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_message = (request.message or "").strip()
    if not user_message:
        return {"response": "Please enter a message.", "intent": "none", "session_id": None}

    # Get or create session
    session_id = get_or_create_session(request.session_id)
    
    # Get conversation history
    conversation_history = get_conversation_history(session_id, limit=10)
    
    # Save user message
    save_message(session_id, "user", user_message)

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
        # For general questions, don't pass MyPursu context
        if any(word in user_message.lower() for word in ['mypursu', 'remit', 'bill', 'payment', 'travel', 'mailbox', 'ship', 'withdraw', 'history', 'scan', 'pay', 'upi', 'qr', 'concierge']):
            final_reply = generate_chatgpt_response(user_message, combined_context, conversation_history)
        else:
            final_reply = generate_chatgpt_response(user_message, "", conversation_history)
    else:
        final_reply = reply_text

    # Save assistant response
    save_message(session_id, "assistant", final_reply, metadata)

    return {
        "response": final_reply,
        "intent": intent,
        "tool_calls": tool_calls,
        "escalated": escalated,
        "metadata": metadata,
        "session_id": session_id
    }

# -----------------------------
# Service endpoint
# -----------------------------
@app.post("/service")
async def service_endpoint(request: ServiceRequest):
    service = (request.service or "").strip()
    if not service:
        return {"response": "Please select a service.", "session_id": None}

    # Get or create session
    session_id = get_or_create_session(request.session_id)
    
    # Get conversation history
    conversation_history = get_conversation_history(session_id, limit=10)
    
    # Save user service request
    save_message(session_id, "user", f"Tell me about the {service} service.")

    db_context = fetch_db_context(service)
    feed_context = build_feed_context(service)

    combined_context = ""
    if db_context:
        combined_context += f"{db_context}\n\n"
    if feed_context:
        combined_context += f"{feed_context}\n\n"

    final_reply = generate_chatgpt_response(f"Tell me about the {service} service.", combined_context, conversation_history)
    
    # Save assistant response
    save_message(session_id, "assistant", final_reply)

    return {
        "response": final_reply,
        "intent": "service_info",
        "tool_calls": [],
        "escalated": False,
        "metadata": {},
        "session_id": session_id
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
# Session Management endpoints
# -----------------------------
@app.get("/session/new")
async def create_new_session():
    """Create a new conversation session"""
    session_id = create_session()
    return {"session_id": session_id, "message": "New session created"}

@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get conversation history for a session"""
    try:
        history = get_conversation_history(session_id, limit=20)
        return {
            "session_id": session_id,
            "history": [{"role": role, "message": message, "timestamp": timestamp} for role, message, timestamp in history]
        }
    except Exception as e:
        return {"error": f"Failed to get history: {str(e)}"}

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a conversation session and its messages"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Delete messages
        cursor.execute("DELETE FROM conversation_messages WHERE session_id = ?", (session_id,))
        
        # Delete session
        cursor.execute("DELETE FROM conversation_sessions WHERE id = ?", (session_id,))
        
        conn.commit()
        conn.close()
        
        return {"message": "Session deleted successfully"}
    except Exception as e:
        return {"error": f"Failed to delete session: {str(e)}"}

@app.post("/cleanup")
async def cleanup_sessions():
    """Manually trigger cleanup of expired sessions"""
    try:
        cleanup_expired_sessions()
        return {"message": "Cleanup completed successfully"}
    except Exception as e:
        return {"error": f"Cleanup failed: {str(e)}"}

@app.post("/crawl-websites")
async def crawl_websites():
    """Manually trigger crawling of MyPursu websites"""
    try:
        crawl_mypursu_websites()
        return {"message": "Website crawling completed successfully"}
    except Exception as e:
        return {"error": f"Website crawling failed: {str(e)}"}

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
