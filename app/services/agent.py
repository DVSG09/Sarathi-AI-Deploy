from typing import Tuple, Dict, List
import re
import logging
import os

# Internal modules
from . import kb as kbmod
from . import tools
from .feed import feed_service

# Azure OpenAI client
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

# -----------------------------
# Azure OpenAI client setup
# -----------------------------
client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY")
)

# -----------------------------
# Intent router
# -----------------------------
def route_intent(text: str) -> str:
    t = text.lower()
    if "policy" in t or ("what" in t and "refund" in t):
        return "faq"
    if any(k in t for k in ["status", "track", "where is my order", "order"]):
        return "status"
    if any(k in t for k in ["reschedule", "appointment", "slot"]):
        return "appointment"
    if any(k in t for k in ["refund", "invoice", "billing", "charge"]):
        return "billing"
    if any(k in t for k in ["password", "account", "login", "profile"]):
        return "account"
    return "faq"

# -----------------------------
# Main message handler
# -----------------------------
def handle_message(user_id: str, text: str, enabled_intents: set[str]) -> Tuple[str, List[Dict], bool, str]:
    intent = route_intent(text)
    if intent not in enabled_intents:
        return ("Sorry, that function is disabled. I can answer FAQs.", [], False, "faq")

    tool_calls: List[Dict] = []
    escalated: bool = False

    # --- STATUS ---
    if intent == "status":
        m = re.search(r'\bORD[0-9]+\b', text.upper())
        order_id = m.group(0) if m else None
        if not order_id:
            return ("I can check your order. Please share the Order ID (e.g., ORD123).", [], False, intent)
        res = tools.get_order_status(order_id)
        tool_calls.append({"name": "orders.get_status", "args": {"order_id": order_id}})
        if not res.get("found"):
            return (f"I couldn't find order {order_id}. Want me to create a support ticket?", tool_calls, True, intent)
        return (f"Order {order_id}: {res['status']}. ETA ~{res['eta_days']} day(s).", tool_calls, False, intent)

    # --- APPOINTMENT ---
    if intent == "appointment":
        words = text.split()
        apt_id = next((w for w in words if w.upper().startswith("APT")), None)
        new_slot = next((w for w in words if "T" in w and ":" in w), None)
        if not apt_id or not new_slot:
            return ("To reschedule, send: APT<id> and ISO time, e.g., APT123 2025-08-01T10:00", [], False, intent)
        res = tools.reschedule_appointment(apt_id, new_slot)
        tool_calls.append({"name": "appointments.reschedule", "args": {"appointment_id": apt_id, "new_slot": new_slot}})
        if res.get("ok"):
            return (f"Rescheduled {apt_id} to {new_slot}. You'll receive a confirmation shortly.", tool_calls, False, intent)
        return ("I couldn't reschedule right now; connecting you to an agent.", tool_calls, True, intent)

    # --- BILLING ---
    if intent == "billing":
        amount = next((float(w) for w in text.replace("$", " ").split() if w.replace('.', '', 1).isdigit()), 0.0)
        case = tools.create_billing_case(user_id, amount, reason="user_request")
        tool_calls.append({"name": "billing.create_case", "args": {"user_id": user_id, "amount": amount}})
        return (f"I opened billing case {case['case_id']} for ${amount:.2f}. An agent will review it.", tool_calls, False, intent)

    # --- ACCOUNT ---
    if intent == "account":
        tip = tools.get_account_help("password")
        tool_calls.append({"name": "account.help", "args": {"topic": "password"}})
        return (tip.get("tip", "Here is some account help."), tool_calls, False, intent)

    # --- FAQ / KB / Feed / ChatGPT fallback ---
    if intent == "faq":
        try:
            # 1️⃣ Feed search
            db_results = getattr(feed_service, "query_feed_by_keyword", lambda text, limit: [])(text, limit=3)
            if db_results:
                reply_text = "\n\n".join(f"{entry.get('title','')}: {entry.get('content','')}" for entry in db_results)
                return reply_text, tool_calls, False, "db"

            # 2️⃣ Hybrid KB search
            context = getattr(kbmod, "get_relevant_context", lambda text, max_chars: "")(text, max_chars=300)
            hybrid_hit = getattr(kbmod, "search_hybrid_kb", lambda text, top_k: [])(text, top_k=1)
            if hybrid_hit:
                title, ans = hybrid_hit[0]
                response = f"{ans}\n\nAdditional context: {context}" if context and context not in ans else ans
                return response, tool_calls, False, "faq"

            # 3️⃣ Basic KB
            basic_hit = getattr(kbmod, "search_kb", lambda text, top_k: [])(text, top_k=1)
            if basic_hit:
                _, ans = basic_hit[0]
                return ans, tool_calls, False, "faq"

            # 4️⃣ Fallback to Azure OpenAI ChatGPT
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                messages=[{"role": "user", "content": text}],
                temperature=0.8,
                max_tokens=150
            )
            reply_text = response.choices[0].message.content
            return reply_text, tool_calls, False, "chatgpt"

        except Exception as e:
            logger.error(f"Error fetching feed/KB/ChatGPT: {e}")
            return ("Oops! Something went wrong. Please try again later.", tool_calls, True, "error")

# -----------------------------
# Enhanced response with metadata
# -----------------------------
def get_enhanced_response(user_id: str, text: str, enabled_intents: set[str]) -> Tuple[str, List[Dict], bool, str, Dict]:
    reply, tool_calls, escalated, intent = handle_message(user_id, text, enabled_intents)
    feed_stats_func = getattr(kbmod, "get_feed_stats", lambda: {"feed_available": False})
    metadata = {
        "intent": intent,
        "escalated": escalated,
        "tool_calls_count": len(tool_calls),
        "feed_available": feed_stats_func().get("feed_available", False)
    }
    return reply, tool_calls, escalated, intent, metadata
