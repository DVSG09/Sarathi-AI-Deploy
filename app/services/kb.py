from typing import Optional, Tuple, List
from .feed import feed_service
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Tiny in-memory KB. Replace with RAG later.
KB = [
    ("refund_policy", "Refunds are eligible within 7 days of purchase if unused."),
    ("reschedule_policy", "Appointments can be rescheduled up to 24 hours before the slot."),
    ("password_reset", "Use the Forgot Password link; a reset email/SMS will be sent."),
    ("shipping_eta", "Standard delivery ETA is 3-5 business days."),
]

def search_kb(query: str, top_k: int = 1) -> List[Tuple[str, str]]:
    """Search the basic knowledge base"""
    q = query.lower()
    scored = []
    for k, v in KB:
        score = sum(int(w in (k + " " + v).lower()) for w in q.split())
        scored.append((score, (k, v)))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [kv for _, kv in scored[:top_k]]

def search_feed_kb(query: str, top_k: int = 3) -> List[Tuple[str, str]]:
    """
    Search the feed-based knowledge base using semantic search
    Returns list of (title, content) tuples
    """
    try:
        # Search feed entries
        results = feed_service.search_feed_entries(query, top_k)
        
        # Convert to (title, content) format for compatibility
        feed_results = []
        for result in results:
            # Use a snippet of content for better context
            content_snippet = result.content[:200] + "..." if len(result.content) > 200 else result.content
            feed_results.append((result.title, content_snippet))
        
        return feed_results
    except Exception as e:
        logger.error(f"Error searching feed KB: {e}")
        return []

def search_hybrid_kb(query: str, top_k: int = 3) -> List[Tuple[str, str]]:
    """
    Hybrid search combining basic KB and feed KB
    Returns combined results with feed results prioritized
    """
    try:
        # Get feed results (semantic search)
        feed_results = search_feed_kb(query, top_k)
        
        # Get basic KB results (keyword search)
        basic_results = search_kb(query, top_k)
        
        # Combine results, prioritizing feed results
        combined_results = []
        
        # Add feed results first (they're more comprehensive)
        combined_results.extend(feed_results)
        
        # Add basic KB results if we have room
        remaining_slots = top_k - len(feed_results)
        if remaining_slots > 0:
            combined_results.extend(basic_results[:remaining_slots])
        
        return combined_results[:top_k]
        
    except Exception as e:
        logger.error(f"Error in hybrid KB search: {e}")
        # Fallback to basic search
        return search_kb(query, top_k)

def get_relevant_context(query: str, max_chars: int = 500) -> str:
    """
    Get relevant context from both KB and feed for chatbot responses
    Returns formatted context string
    """
    try:
        # Get hybrid search results
        results = search_hybrid_kb(query, top_k=2)
        
        if not results:
            return ""
        
        # Format context
        context_parts = []
        for title, content in results:
            context_parts.append(f"From '{title}': {content}")
        
        context = " ".join(context_parts)
        
        # Truncate if too long
        if len(context) > max_chars:
            context = context[:max_chars-3] + "..."
        
        return context
        
    except Exception as e:
        logger.error(f"Error getting relevant context: {e}")
        return ""

def get_feed_stats() -> dict:
    """Get statistics about the feed knowledge base"""
    try:
        stats = feed_service.list_feed_entries(page=1, page_size=1, status="active")
        return {
            "total_feed_entries": stats.total,
            "feed_available": stats.total > 0
        }
    except Exception as e:
        logger.error(f"Error getting feed stats: {e}")
        return {
            "total_feed_entries": 0,
            "feed_available": False
        }

# ------------------ NEW FUNCTION ------------------
def fetch_website_content(url: str) -> str:
    """
    Fetch the text content of a webpage (like main site or FAQ) for KB ingestion.
    """
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract visible text
        text = soup.get_text(separator=" ", strip=True)
        return text
    except Exception as e:
        logger.error(f"Error fetching website content from {url}: {e}")
        return ""
