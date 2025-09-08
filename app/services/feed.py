from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import sqlite3  # For direct SQLite queries
from .database import db
from .embeddings import embedding_service
from ..schemas import FeedEntryCreate, FeedEntryUpdate, FeedEntryResponse, FeedEntryListResponse

logger = logging.getLogger(__name__)

class FeedService:
    """Service for managing feed entries with vector embeddings"""
    
    # --- Existing methods (create, get, update, delete, list, search, batch) ---
    # [Keep all your current methods as-is]

    # ------------------ NEW METHOD ------------------
    def query_feed_by_keyword(self, keyword: str, limit: int = 5) -> List[FeedEntryResponse]:
        """
        Query the SQLite DB directly for entries containing the keyword in title, content, or tags.
        Returns top `limit` results as FeedEntryResponse objects.
        """
        results = []
        try:
            conn = sqlite3.connect("sarathi_feed.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, title, content, source, entry_type, tags, metadata, status, created_at, updated_at
                FROM feed_entries
                WHERE status='active' AND 
                      (title LIKE ? OR content LIKE ? OR tags LIKE ?)
                LIMIT ?
                """,
                ('%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%', limit)
            )
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                entry_id, title, content, source, entry_type, tags, metadata, status, created_at, updated_at = row
                results.append(FeedEntryResponse(
                    id=entry_id,
                    title=title,
                    content=content,
                    source=source,
                    entry_type=entry_type,
                    tags=eval(tags) if tags else [],
                    metadata=eval(metadata) if metadata else {},
                    status=status,
                    created_at=datetime.fromisoformat(created_at),
                    updated_at=datetime.fromisoformat(updated_at),
                    chunks_count=db.get_chunk_count(entry_id)
                ))
            
        except Exception as e:
            logger.error(f"Error querying feed by keyword '{keyword}': {e}")
        
        return results

# Global feed service instance
feed_service = FeedService()
