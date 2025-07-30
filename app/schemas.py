from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    user_id: str = Field(..., examples=["user_123"])
    message: str = Field(..., examples=["Where is my order?"])

class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any] = {}

class ChatResponse(BaseModel):
    reply: str
    tool_calls: List[ToolCall] = []
    latency_ms: int
    escalated: bool = False
    intent: Optional[str] = None
