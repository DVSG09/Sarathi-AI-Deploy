from typing import Optional, Tuple, List

# Tiny in-memory KB. Replace with RAG later.
KB = [
    ("refund_policy", "Refunds are eligible within 7 days of purchase if unused."),
    ("reschedule_policy", "Appointments can be rescheduled up to 24 hours before the slot."),
    ("password_reset", "Use the Forgot Password link; a reset email/SMS will be sent."),
    ("shipping_eta", "Standard delivery ETA is 3-5 business days."),
]

def search_kb(query: str, top_k: int = 1) -> List[Tuple[str, str]]:
    q = query.lower()
    scored = []
    for k, v in KB:
        score = sum(int(w in (k + " " + v).lower()) for w in q.split())
        scored.append((score, (k, v)))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [kv for _, kv in scored[:top_k]]
