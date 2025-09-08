from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

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

# Feed Management Schemas
class FeedEntryType(str, Enum):
    TEXT = "text"
    URL = "url"
    FILE = "file"
    DOCUMENT = "document"

class FeedEntryStatus(str, Enum):
    ACTIVE = "active"
    DELETED = "deleted"
    ARCHIVED = "archived"

class FeedEntryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, examples=["Product Documentation"])
    content: str = Field(..., min_length=1, examples=["This is the content of the feed entry..."])
    source: Optional[str] = Field(None, max_length=500, examples=["https://example.com/doc"])
    entry_type: FeedEntryType = Field(FeedEntryType.TEXT, examples=[FeedEntryType.TEXT])
    tags: List[str] = Field(default_factory=list, examples=[["documentation", "product"]])
    metadata: Dict[str, Any] = Field(default_factory=dict, examples=[{"author": "John Doe", "version": "1.0"}])

class FeedEntryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, examples=["Updated Product Documentation"])
    content: Optional[str] = Field(None, min_length=1, examples=["Updated content..."])
    source: Optional[str] = Field(None, max_length=500, examples=["https://example.com/updated-doc"])
    tags: Optional[List[str]] = Field(None, examples=[["documentation", "product", "updated"]])
    metadata: Optional[Dict[str, Any]] = Field(None, examples=[{"author": "Jane Doe", "version": "2.0"}])

class FeedEntryResponse(BaseModel):
    id: str
    title: str
    content: str
    source: Optional[str]
    entry_type: FeedEntryType
    tags: List[str]
    metadata: Dict[str, Any]
    status: FeedEntryStatus
    created_at: datetime
    updated_at: datetime
    chunks_count: int = Field(0, description="Number of content chunks")

class FeedEntryListResponse(BaseModel):
    entries: List[FeedEntryResponse]
    total: int
    page: int
    page_size: int

class FeedSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, examples=["product documentation"])
    limit: int = Field(10, ge=1, le=100, examples=[10])
    tags: Optional[List[str]] = Field(None, examples=[["documentation"]])

class FeedSearchResponse(BaseModel):
    results: List[FeedEntryResponse]
    total_found: int
    query: str

class DeleteRequest(BaseModel):
    hard_delete: bool = Field(False, description="Permanently delete instead of soft delete")
