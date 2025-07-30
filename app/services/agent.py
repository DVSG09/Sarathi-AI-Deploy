from typing import Tuple, Dict, List
from . import kb as kbmod
from . import tools

# Very simfrom typing import Tuple, Dict, List
import re
from . import kb as kbmod
from . import tools

# Improved intent router to handle refund policy questions better
def route_intent(text: str) -> str:
    t = text.lower()

    # FAQ-first heuristic: questions about "policy" or refund FAQ
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

def handle_message(user_id: str, text: str, enabled_intents: set[str]) -> Tuple[str, List[Dict], bool, str]:
    intent = route_intent(text)
    if intent not in enabled_intents:
        return ("Sorry, that function is disabled right now. I can answer FAQs.", [], False, "faq")

    tool_calls = []
    escalated = False

    if intent == "status":
        # Improved parse for order id using regex like ORD123
        order_id = None
        m = re.search(r'\bORD[0-9]+\b', text.upper())
        if m:
            order_id = m.group(0)

        if not order_id:
            return ("I can check your order. Please share the Order ID (e.g., ORD123).", [], False, intent)
        res = tools.get_order_status(order_id)
        tool_calls.append({"name": "orders.get_status", "args": {"order_id": order_id}})
        if not res.get("found"):
            return (f"I couldn't find order {order_id}. Want me to create a support ticket?", tool_calls, True, intent)
        return (f"Order {order_id}: {res['status']}. ETA ~{res['eta_days']} day(s).", tool_calls, False, intent)

    if intent == "appointment":
        # naive parse for an appointment id like APT123 and slot like 2025-08-01T10:00
        words = text.split()
        apt_id = next((w for w in words if w.upper().startswith("APT")), None)
        new_slot = next((w for w in words if "T" in w and ":" in w), None)
        if not apt_id or not new_slot:
            return ("To reschedule, send: APT<id> and ISO time, e.g., APT123 2025-08-01T10:00", [], False, intent)
        res = tools.reschedule_appointment(apt_id, new_slot)
        tool_calls.append({"name": "appointments.reschedule", "args": {"appointment_id": apt_id, "new_slot": new_slot}})
        if res.get("ok"):
            return (f"Rescheduled {apt_id} to {new_slot}. You’ll receive a confirmation shortly.", tool_calls, False, intent)
        return ("I couldn't reschedule right now; connecting you to an agent.", tool_calls, True, intent)

    if intent == "billing":
        # naive parse for amount
        amount = None
        for w in text.replace("$", " ").split():
            try:
                amount = float(w)
                break
            except: ...
        case = tools.create_billing_case(user_id, amount or 0.0, reason="user_request")
        tool_calls.append({"name": "billing.create_case", "args": {"user_id": user_id, "amount": amount or 0.0}})
        return (f"I opened billing case {case['case_id']} for ${amount or 0:.2f}. An agent will review it.", tool_calls, False, intent)

    if intent == "account":
        tip = tools.get_account_help("password")
        tool_calls.append({"name": "account.help", "args": {"topic": "password"}})
        return (tip["tip"], tool_calls, False, intent)

    # Fallback: FAQ via KB
    hit = kbmod.search_kb(text, top_k=1)
    if hit:
        _, ans = hit[0]
        return (ans, tool_calls, False, "faq")
    return ("I’m not sure. I can connect you to a human agent.", tool_calls, True, "faq")

