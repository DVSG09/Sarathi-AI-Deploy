import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import FeedEntryCreate, FeedEntryType, FeedEntryUpdate
import tempfile
import os

client = TestClient(app)

# Test data
sample_feed_entry = {
    "title": "Test Documentation",
    "content": "This is a test document for the feed management system. It contains information about testing procedures and best practices.",
    "source": "https://example.com/test-doc",
    "entry_type": "document",
    "tags": ["testing", "documentation"],
    "metadata": {"author": "Test User", "version": "1.0"}
}

sample_feed_entry_2 = {
    "title": "Product Guide",
    "content": "This is a product guide that explains how to use our software. It includes step-by-step instructions and troubleshooting tips.",
    "source": "https://example.com/product-guide",
    "entry_type": "document",
    "tags": ["product", "guide", "instructions"],
    "metadata": {"author": "Product Team", "version": "2.0"}
}

class TestFeedManagement:
    """Test suite for feed management functionality"""
    
    def test_create_feed_entry(self):
        """Test creating a new feed entry"""
        response = client.post("/api/v1/feed/", json=sample_feed_entry)
        assert response.status_code == 201
        data = response.json()
        
        assert data["title"] == sample_feed_entry["title"]
        assert data["content"] == sample_feed_entry["content"]
        assert data["source"] == sample_feed_entry["source"]
        assert data["entry_type"] == sample_feed_entry["entry_type"]
        assert data["tags"] == sample_feed_entry["tags"]
        assert data["metadata"] == sample_feed_entry["metadata"]
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["chunks_count"] > 0
    
    def test_create_feed_entry_minimal(self):
        """Test creating a feed entry with minimal required fields"""
        minimal_entry = {
            "title": "Minimal Entry",
            "content": "This is a minimal entry with only required fields."
        }
        
        response = client.post("/api/v1/feed/", json=minimal_entry)
        assert response.status_code == 201
        data = response.json()
        
        assert data["title"] == minimal_entry["title"]
        assert data["content"] == minimal_entry["content"]
        assert data["entry_type"] == "text"  # default value
        assert data["tags"] == []  # default empty list
        assert data["metadata"] == {}  # default empty dict
    
    def test_create_feed_entry_validation(self):
        """Test validation errors for feed entry creation"""
        # Test empty title
        invalid_entry = sample_feed_entry.copy()
        invalid_entry["title"] = ""
        
        response = client.post("/api/v1/feed/", json=invalid_entry)
        assert response.status_code == 422
        
        # Test empty content
        invalid_entry = sample_feed_entry.copy()
        invalid_entry["content"] = ""
        
        response = client.post("/api/v1/feed/", json=invalid_entry)
        assert response.status_code == 422
    
    def test_get_feed_entry(self):
        """Test retrieving a specific feed entry"""
        # First create an entry
        create_response = client.post("/api/v1/feed/", json=sample_feed_entry)
        assert create_response.status_code == 201
        entry_id = create_response.json()["id"]
        
        # Then retrieve it
        response = client.get(f"/api/v1/feed/{entry_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == entry_id
        assert data["title"] == sample_feed_entry["title"]
        assert data["content"] == sample_feed_entry["content"]
    
    def test_get_feed_entry_not_found(self):
        """Test retrieving a non-existent feed entry"""
        response = client.get("/api/v1/feed/non-existent-id")
        assert response.status_code == 404
    
    def test_update_feed_entry(self):
        """Test updating a feed entry"""
        # First create an entry
        create_response = client.post("/api/v1/feed/", json=sample_feed_entry)
        assert create_response.status_code == 201
        entry_id = create_response.json()["id"]
        
        # Update the entry
        update_data = {
            "title": "Updated Test Documentation",
            "content": "This is the updated content with new information.",
            "tags": ["testing", "documentation", "updated"]
        }
        
        response = client.put(f"/api/v1/feed/{entry_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == update_data["title"]
        assert data["content"] == update_data["content"]
        assert data["tags"] == update_data["tags"]
        assert data["id"] == entry_id
    
    def test_update_feed_entry_not_found(self):
        """Test updating a non-existent feed entry"""
        update_data = {"title": "Updated Title"}
        response = client.put("/api/v1/feed/non-existent-id", json=update_data)
        assert response.status_code == 404
    
    def test_delete_feed_entry_soft(self):
        """Test soft deleting a feed entry"""
        # First create an entry
        create_response = client.post("/api/v1/feed/", json=sample_feed_entry)
        assert create_response.status_code == 201
        entry_id = create_response.json()["id"]
        
        # Soft delete the entry
        response = client.delete(f"/api/v1/feed/{entry_id}?hard_delete=false")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["entry_id"] == entry_id
        
        # Verify it's not retrievable
        get_response = client.get(f"/api/v1/feed/{entry_id}")
        assert get_response.status_code == 404
    
    def test_delete_feed_entry_hard(self):
        """Test hard deleting a feed entry"""
        # First create an entry
        create_response = client.post("/api/v1/feed/", json=sample_feed_entry)
        assert create_response.status_code == 201
        entry_id = create_response.json()["id"]
        
        # Hard delete the entry
        response = client.delete(f"/api/v1/feed/{entry_id}?hard_delete=true")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["entry_id"] == entry_id
        
        # Verify it's not retrievable
        get_response = client.get(f"/api/v1/feed/{entry_id}")
        assert get_response.status_code == 404
    
    def test_delete_feed_entry_not_found(self):
        """Test deleting a non-existent feed entry"""
        response = client.delete("/api/v1/feed/non-existent-id?hard_delete=false")
        assert response.status_code == 404
    
    def test_list_feed_entries(self):
        """Test listing feed entries with pagination"""
        # Create multiple entries
        client.post("/api/v1/feed/", json=sample_feed_entry)
        client.post("/api/v1/feed/", json=sample_feed_entry_2)
        
        response = client.get("/api/v1/feed/")
        assert response.status_code == 200
        data = response.json()
        
        assert "entries" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["entries"]) > 0
    
    def test_list_feed_entries_pagination(self):
        """Test pagination for feed entries"""
        # Create multiple entries
        for i in range(15):
            entry = sample_feed_entry.copy()
            entry["title"] = f"Entry {i}"
            client.post("/api/v1/feed/", json=entry)
        
        # Test first page
        response = client.get("/api/v1/feed/?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) <= 5
        assert data["page"] == 1
        assert data["page_size"] == 5
    
    def test_search_feed_entries(self):
        """Test searching feed entries"""
        # Create entries
        client.post("/api/v1/feed/", json=sample_feed_entry)
        client.post("/api/v1/feed/", json=sample_feed_entry_2)
        
        # Search for "testing"
        search_request = {
            "query": "testing",
            "limit": 10
        }
        
        response = client.post("/api/v1/feed/search", json=search_request)
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total_found" in data
        assert "query" in data
        assert data["query"] == "testing"
        assert len(data["results"]) > 0
    
    def test_search_feed_entries_with_tags(self):
        """Test searching feed entries with tag filtering"""
        # Create entries
        client.post("/api/v1/feed/", json=sample_feed_entry)
        client.post("/api/v1/feed/", json=sample_feed_entry_2)
        
        # Search with tag filter
        search_request = {
            "query": "documentation",
            "limit": 10,
            "tags": ["testing"]
        }
        
        response = client.post("/api/v1/feed/search", json=search_request)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["results"]) > 0
        # Verify all results have the "testing" tag
        for result in data["results"]:
            assert "testing" in result["tags"]
    
    def test_get_feed_entry_chunks(self):
        """Test retrieving chunks for a feed entry"""
        # Create an entry
        create_response = client.post("/api/v1/feed/", json=sample_feed_entry)
        assert create_response.status_code == 201
        entry_id = create_response.json()["id"]
        
        # Get chunks
        response = client.get(f"/api/v1/feed/{entry_id}/chunks")
        assert response.status_code == 200
        data = response.json()
        
        assert "entry_id" in data
        assert "chunks" in data
        assert "total_chunks" in data
        assert data["entry_id"] == entry_id
        assert len(data["chunks"]) > 0
        assert data["total_chunks"] == len(data["chunks"])
    
    def test_batch_create_feed_entries(self):
        """Test batch creating multiple feed entries"""
        batch_entries = [
            sample_feed_entry,
            sample_feed_entry_2,
            {
                "title": "Batch Entry 3",
                "content": "This is the third batch entry for testing purposes."
            }
        ]
        
        response = client.post("/api/v1/feed/batch", json=batch_entries)
        assert response.status_code == 201
        data = response.json()
        
        assert len(data) == 3
        assert all("id" in entry for entry in data)
        assert all(entry["status"] == "active" for entry in data)
    
    def test_batch_create_feed_entries_limit(self):
        """Test batch size limit"""
        # Create more than 50 entries
        batch_entries = []
        for i in range(51):
            entry = sample_feed_entry.copy()
            entry["title"] = f"Batch Entry {i}"
            batch_entries.append(entry)
        
        response = client.post("/api/v1/feed/batch", json=batch_entries)
        assert response.status_code == 400
        assert "Batch size cannot exceed 50" in response.json()["detail"]
    
    def test_get_feed_stats(self):
        """Test getting feed statistics"""
        # Create some entries
        client.post("/api/v1/feed/", json=sample_feed_entry)
        client.post("/api/v1/feed/", json=sample_feed_entry_2)
        
        response = client.get("/api/v1/feed/stats/summary")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_active_entries" in data
        assert "total_deleted_entries" in data
        assert "total_entries" in data
        assert data["total_active_entries"] >= 2
        assert data["total_entries"] >= 2

class TestFeedIntegration:
    """Test integration between feed management and chat system"""
    
    def test_chat_with_feed_content(self):
        """Test that chat can access feed content"""
        # Create a feed entry
        client.post("/api/v1/feed/", json=sample_feed_entry)
        
        # Test chat endpoint (legacy)
        chat_request = {"message": "Tell me about testing procedures"}
        response = client.post("/chat", json=chat_request)
        assert response.status_code == 200
        
        # Test new chat endpoint
        chat_request = {
            "user_id": "test_user",
            "message": "Tell me about testing procedures"
        }
        response = client.post("/api/v1/chat", json=chat_request)
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "latency_ms" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0" 