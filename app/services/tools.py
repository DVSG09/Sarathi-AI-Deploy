from typing import Optional, Dict

# Tool stubs. Replace with real integrations later.
def get_order_status(order_id: str) -> Dict:
    # Simulated records
    db = {"ORD123": {"status": "Out for delivery", "eta_days": 1}}
    data = db.get(order_id.upper())
    if not data:
        return {"found": False}
    return {"found": True, **data}

def reschedule_appointment(appointment_id: str, new_slot: str) -> Dict:
    return {"ok": True, "appointment_id": appointment_id, "new_slot": new_slot}

def create_billing_case(user_id: str, amount: float, reason: str) -> Dict:
    return {"case_id": "BILL-" + user_id[-4:], "status": "open", "amount": amount, "reason": reason}

def get_account_help(topic: str) -> Dict:
    if topic.lower() == "password":
        return {"tip": "Use the Forgot Password option to receive a reset link."}
    return {"tip": "Update profile from Account > Settings."}
