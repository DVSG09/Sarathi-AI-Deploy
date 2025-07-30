from fastapi import APIRouter, Depends
from .schemas import ChatRequest, ChatResponse
from .services.agent import handle_message
from .config import settings
from .services.telemetry import timer

router = APIRouter(prefix="/api/v1", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    with timer() as elapsed:
        reply, tool_calls, escalated, intent = handle_message(req.user_id, req.message, settings.enabled_intents)
        latency_ms = elapsed()
        return ChatResponse(
            reply=reply,
            tool_calls=tool_calls,
            latency_ms=latency_ms,
            escalated=escalated,
            intent=intent
        )
