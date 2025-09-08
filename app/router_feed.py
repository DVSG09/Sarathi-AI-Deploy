from fastapi import APIRouter, HTTPException, Query
from typing import List
import logging
from .schemas import (
    FeedEntryCreate, FeedEntryUpdate, FeedEntryResponse, FeedEntryListResponse,
    FeedSearchRequest, FeedSearchResponse
)
from .services.feed import feed_service
from .kb import fetch_website_content  # Import our crawler function

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/feed", tags=["feed"])

@router.post("/", response_model=FeedEntryResponse, status_code=201)
async def create_feed_entry(entry_data: FeedEntryCreate):
    try:
        result = feed_service.create_feed_entry(entry_data)
        logger.info(f"Created feed entry: {result.id}")
        return result
    except Exception as e:
        logger.error(f"Error creating feed entry: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create feed entry: {str(e)}")

@router.get("/{entry_id}", response_model=FeedEntryResponse)
async def get_feed_entry(entry_id: str):
    try:
        entry = feed_service.get_feed_entry(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Feed entry not found")
        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feed entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve feed entry: {str(e)}")

@router.put("/{entry_id}", response_model=FeedEntryResponse)
async def update_feed_entry(entry_id: str, update_data: FeedEntryUpdate):
    try:
        entry = feed_service.update_feed_entry(entry_id, update_data)
        if not entry:
            raise HTTPException(status_code=404, detail="Feed entry not found")
        logger.info(f"Updated feed entry: {entry_id}")
        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feed entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update feed entry: {str(e)}")

@router.delete("/{entry_id}")
async def delete_feed_entry(entry_id: str, hard_delete: bool = Query(False, description="Permanently delete instead of soft delete")):
    try:
        success = feed_service.delete_feed_entry(entry_id, hard_delete)
        if not success:
            raise HTTPException(status_code=404, detail="Feed entry not found")
        delete_type = "hard" if hard_delete else "soft"
        logger.info(f"{delete_type.capitalize()} deleted feed entry: {entry_id}")
        return {"status": "success", "message": f"Feed entry {delete_type} deleted successfully", "entry_id": entry_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feed entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete feed entry: {str(e)}")

@router.get("/", response_model=FeedEntryListResponse)
async def list_feed_entries(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), status: str = Query("active")):
    try:
        result = feed_service.list_feed_entries(page, page_size, status)
        return result
    except Exception as e:
        logger.error(f"Error listing feed entries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list feed entries: {str(e)}")

@router.post("/search", response_model=FeedSearchResponse)
async def search_feed_entries(search_request: FeedSearchRequest):
    try:
        results = feed_service.search_feed_entries(search_request.query, search_request.limit, search_request.tags)
        return FeedSearchResponse(results=results, total_found=len(results), query=search_request.query)
    except Exception as e:
        logger.error(f"Error searching feed entries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search feed entries: {str(e)}")

@router.get("/{entry_id}/chunks")
async def get_feed_entry_chunks(entry_id: str):
    try:
        entry = feed_service.get_feed_entry(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Feed entry not found")
        chunks = feed_service.get_feed_entry_chunks(entry_id)
        return {"entry_id": entry_id, "chunks": chunks, "total_chunks": len(chunks)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chunks for entry {entry_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chunks: {str(e)}")

@router.post("/batch", response_model=List[FeedEntryResponse], status_code=201)
async def batch_create_feed_entries(entries_data: List[FeedEntryCreate]):
    try:
        if len(entries_data) > 50:
            raise HTTPException(status_code=400, detail="Batch size cannot exceed 50 entries")
        results = feed_service.batch_create_entries(entries_data)
        logger.info(f"Batch created {len(results)} feed entries")
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error batch creating feed entries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to batch create feed entries: {str(e)}")

@router.get("/stats/summary")
async def get_feed_stats():
    try:
        active_entries = feed_service.list_feed_entries(page=1, page_size=1, status="active")
        deleted_entries = feed_service.list_feed_entries(page=1, page_size=1, status="deleted")
        return {"total_active_entries": active_entries.total, "total_deleted_entries": deleted_entries.total, "total_entries": active_entries.total + deleted_entries.total}
    except Exception as e:
        logger.error(f"Error getting feed stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get feed statistics: {str(e)}")

# ------------------ NEW CRAWL ENDPOINT ------------------
@router.post("/crawl", response_model=List[FeedEntryResponse])
async def crawl_website(urls: List[str]):
    """
    Crawl one or more URLs, fetch the text content, and save as feed entries.
    """
    created_entries = []
    for url in urls:
        content = fetch_website_content(url)
        if not content:
            logger.warning(f"No content fetched from {url}")
            continue
        
        entry_data = FeedEntryCreate(
            title=f"Crawled content from {url}",
            content=content,
            source=url,
            entry_type="web",
            tags=["crawl"]
        )
        created_entry = feed_service.create_feed_entry(entry_data)
        created_entries.append(created_entry)
        logger.info(f"Saved crawled content from {url} to feed DB")
    
    if not created_entries:
        raise HTTPException(status_code=400, detail="No content was crawled or saved.")
    
    return created_entries
