import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
import os
from pathlib import Path

class DatabaseService:
    def __init__(self, db_path: str = "sarathi_feed.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feed_entries (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT,
                    entry_type TEXT NOT NULL,
                    tags TEXT NOT NULL,  -- JSON array
                    metadata TEXT NOT NULL,  -- JSON object
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feed_chunks (
                    id TEXT PRIMARY KEY,
                    entry_id TEXT NOT NULL,
                    chunk_text TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    embedding TEXT,  -- JSON array of floats
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (entry_id) REFERENCES feed_entries (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feed_entries_status ON feed_entries(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feed_entries_type ON feed_entries(entry_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feed_chunks_entry_id ON feed_chunks(entry_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feed_chunks_embedding ON feed_chunks(embedding)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def create_feed_entry(self, title: str, content: str, source: Optional[str], 
                         entry_type: str, tags: List[str], metadata: Dict[str, Any]) -> str:
        """Create a new feed entry and return its ID"""
        entry_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO feed_entries (id, title, content, source, entry_type, tags, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id, title, content, source, entry_type,
                json.dumps(tags), json.dumps(metadata), now, now
            ))
            conn.commit()
        
        return entry_id
    
    def get_feed_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a feed entry by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM feed_entries WHERE id = ? AND status != 'deleted'
            """, (entry_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row['id'],
                    'title': row['title'],
                    'content': row['content'],
                    'source': row['source'],
                    'entry_type': row['entry_type'],
                    'tags': json.loads(row['tags']),
                    'metadata': json.loads(row['metadata']),
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
        return None
    
    def update_feed_entry(self, entry_id: str, **updates) -> bool:
        """Update a feed entry"""
        if not updates:
            return False
        
        # Build dynamic update query
        set_clauses = []
        values = []
        
        for field, value in updates.items():
            if field in ['title', 'content', 'source', 'entry_type']:
                set_clauses.append(f"{field} = ?")
                values.append(value)
            elif field == 'tags':
                set_clauses.append("tags = ?")
                values.append(json.dumps(value))
            elif field == 'metadata':
                set_clauses.append("metadata = ?")
                values.append(json.dumps(value))
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.append(entry_id)
        
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                UPDATE feed_entries 
                SET {', '.join(set_clauses)}
                WHERE id = ? AND status != 'deleted'
            """, values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_feed_entry(self, entry_id: str, hard_delete: bool = False) -> bool:
        """Delete a feed entry (soft or hard delete)"""
        with self._get_connection() as conn:
            if hard_delete:
                # Hard delete - remove from database completely
                cursor = conn.execute("DELETE FROM feed_entries WHERE id = ?", (entry_id,))
                conn.execute("DELETE FROM feed_chunks WHERE entry_id = ?", (entry_id,))
            else:
                # Soft delete - mark as deleted
                cursor = conn.execute("""
                    UPDATE feed_entries 
                    SET status = 'deleted', updated_at = ? 
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), entry_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def list_feed_entries(self, page: int = 1, page_size: int = 10, 
                         status: str = 'active') -> Dict[str, Any]:
        """List feed entries with pagination"""
        offset = (page - 1) * page_size
        
        with self._get_connection() as conn:
            # Get total count
            count_cursor = conn.execute("""
                SELECT COUNT(*) as total FROM feed_entries WHERE status = ?
            """, (status,))
            total = count_cursor.fetchone()['total']
            
            # Get entries
            cursor = conn.execute("""
                SELECT * FROM feed_entries 
                WHERE status = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (status, page_size, offset))
            
            entries = []
            for row in cursor.fetchall():
                entries.append({
                    'id': row['id'],
                    'title': row['title'],
                    'content': row['content'],
                    'source': row['source'],
                    'entry_type': row['entry_type'],
                    'tags': json.loads(row['tags']),
                    'metadata': json.loads(row['metadata']),
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return {
                'entries': entries,
                'total': total,
                'page': page,
                'page_size': page_size
            }
    
    def search_feed_entries(self, query: str, limit: int = 10, 
                           tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search feed entries by content and tags"""
        with self._get_connection() as conn:
            sql = """
                SELECT * FROM feed_entries 
                WHERE status = 'active' 
                AND (title LIKE ? OR content LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]
            
            if tags:
                # Filter by tags (simple JSON array contains check)
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f"%{json.dumps(tag)[1:-1]}%")  # Remove quotes from JSON string
                sql += f" AND ({' OR '.join(tag_conditions)})"
            
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'title': row['title'],
                    'content': row['content'],
                    'source': row['source'],
                    'entry_type': row['entry_type'],
                    'tags': json.loads(row['tags']),
                    'metadata': json.loads(row['metadata']),
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return results
    
    def save_chunks(self, entry_id: str, chunks: List[Dict[str, Any]]) -> None:
        """Save content chunks with embeddings"""
        with self._get_connection() as conn:
            # Delete existing chunks for this entry
            conn.execute("DELETE FROM feed_chunks WHERE entry_id = ?", (entry_id,))
            
            # Insert new chunks
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO feed_chunks (id, entry_id, chunk_text, chunk_index, embedding, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    chunk_id, entry_id, chunk['text'], i,
                    json.dumps(chunk.get('embedding', [])),
                    datetime.utcnow().isoformat()
                ))
            
            conn.commit()
    
    def get_chunks(self, entry_id: str) -> List[Dict[str, Any]]:
        """Get chunks for a feed entry"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM feed_chunks 
                WHERE entry_id = ? 
                ORDER BY chunk_index
            """, (entry_id,))
            
            chunks = []
            for row in cursor.fetchall():
                chunks.append({
                    'id': row['id'],
                    'chunk_text': row['chunk_text'],
                    'chunk_index': row['chunk_index'],
                    'embedding': json.loads(row['embedding']) if row['embedding'] else None,
                    'created_at': row['created_at']
                })
            
            return chunks
    
    def get_chunk_count(self, entry_id: str) -> int:
        """Get the number of chunks for a feed entry"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as count FROM feed_chunks WHERE entry_id = ?
            """, (entry_id,))
            return cursor.fetchone()['count']

# Global database instance
db = DatabaseService() 