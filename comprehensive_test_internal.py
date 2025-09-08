#!/usr/bin/env python3
"""
Comprehensive Internal Test Script for Sarathi Feed Management System

This script tests all possible scenarios and edge cases using FastAPI's TestClient.
"""

import json
import sys
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from app.main import app

# Create test client
client = TestClient(app)

def print_test_result(test_name: str, success: bool, details: str = ""):
    """Print test result with formatting"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")
    print()

def test_health_endpoint():
    """Test health endpoint"""
    try:
        response = client.get("/health")
        success = response.status_code == 200
        data = response.json() if success else {}
        details = f"Status: {response.status_code}, Version: {data.get('version', 'N/A')}"
        print_test_result("Health Endpoint", success, details)
        return success
    except Exception as e:
        print_test_result("Health Endpoint", False, f"Error: {str(e)}")
        return False

def test_create_feed_entries():
    """Test creating various types of feed entries"""
    test_entries = [
        {
            "title": "Basic Text Entry",
            "content": "This is a simple text entry for testing purposes.",
            "entry_type": "text",
            "tags": ["test", "basic"],
            "metadata": {"author": "Test User"}
        },
        {
            "title": "Document Entry",
            "content": "This is a longer document entry with more detailed content. It contains multiple sentences and should be chunked appropriately for vector embeddings.",
            "entry_type": "document",
            "tags": ["document", "detailed"],
            "metadata": {"author": "Test User", "category": "documentation"}
        },
        {
            "title": "URL Entry",
            "content": "Content from a URL source with technical information about APIs and integrations.",
            "source": "https://example.com/api-docs",
            "entry_type": "url",
            "tags": ["url", "api", "technical"],
            "metadata": {"source_type": "webpage"}
        },
        {
            "title": "File Entry",
            "content": "Content extracted from an uploaded file with file-specific information and formatting.",
            "entry_type": "file",
            "tags": ["file", "upload"],
            "metadata": {"file_type": "pdf", "size": "2.5MB"}
        }
    ]
    
    created_entries = []
    
    for i, entry in enumerate(test_entries):
        try:
            response = client.post("/api/v1/feed/", json=entry)
            success = response.status_code == 201
            if success:
                data = response.json()
                created_entries.append(data)
                details = f"ID: {data['id']}, Chunks: {data['chunks_count']}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            print_test_result(f"Create Entry {i+1}: {entry['title']}", success, details)
        except Exception as e:
            print_test_result(f"Create Entry {i+1}: {entry['title']}", False, f"Error: {str(e)}")
    
    return created_entries

def test_get_feed_entries(entry_ids: List[str]):
    """Test retrieving feed entries"""
    for i, entry_id in enumerate(entry_ids):
        try:
            response = client.get(f"/api/v1/feed/{entry_id}")
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Title: {data['title']}, Status: {data['status']}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            print_test_result(f"Get Entry {i+1}", success, details)
        except Exception as e:
            print_test_result(f"Get Entry {i+1}", False, f"Error: {str(e)}")

def test_update_feed_entries(entry_ids: List[str]):
    """Test updating feed entries"""
    updates = [
        {"title": "Updated Basic Entry", "tags": ["test", "basic", "updated"]},
        {"content": "This is the updated content with new information and additional details.", "metadata": {"author": "Test User", "updated": True}},
        {"source": "https://example.com/updated-api-docs", "tags": ["url", "api", "technical", "updated"]},
        {"title": "Updated File Entry", "entry_type": "document"}
    ]
    
    for i, (entry_id, update) in enumerate(zip(entry_ids, updates)):
        try:
            response = client.put(f"/api/v1/feed/{entry_id}", json=update)
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Updated: {list(update.keys())}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            print_test_result(f"Update Entry {i+1}", success, details)
        except Exception as e:
            print_test_result(f"Update Entry {i+1}", False, f"Error: {str(e)}")

def test_list_feed_entries():
    """Test listing feed entries with pagination"""
    test_cases = [
        {"page": 1, "page_size": 5, "status": "active"},
        {"page": 1, "page_size": 2, "status": "active"},
        {"page": 2, "page_size": 2, "status": "active"},
    ]
    
    for i, params in enumerate(test_cases):
        try:
            response = client.get("/api/v1/feed/", params=params)
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Page: {data['page']}, Total: {data['total']}, Entries: {len(data['entries'])}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            print_test_result(f"List Entries {i+1} (Page {params['page']}, Size {params['page_size']})", success, details)
        except Exception as e:
            print_test_result(f"List Entries {i+1}", False, f"Error: {str(e)}")

def test_search_feed_entries():
    """Test searching feed entries"""
    search_queries = [
        {"query": "test", "limit": 5},
        {"query": "document", "limit": 3},
        {"query": "technical", "limit": 5, "tags": ["technical"]},
        {"query": "updated", "limit": 10},
        {"query": "nonexistent content", "limit": 5},
    ]
    
    for i, query in enumerate(search_queries):
        try:
            response = client.post("/api/v1/feed/search", json=query)
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Found: {data['total_found']}, Query: '{data['query']}'"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            print_test_result(f"Search {i+1}: '{query['query']}'", success, details)
        except Exception as e:
            print_test_result(f"Search {i+1}", False, f"Error: {str(e)}")

def test_get_chunks(entry_ids: List[str]):
    """Test retrieving chunks for feed entries"""
    for i, entry_id in enumerate(entry_ids):
        try:
            response = client.get(f"/api/v1/feed/{entry_id}/chunks")
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Chunks: {data['total_chunks']}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            print_test_result(f"Get Chunks {i+1}", success, details)
        except Exception as e:
            print_test_result(f"Get Chunks {i+1}", False, f"Error: {str(e)}")

def test_batch_create():
    """Test batch creation of feed entries"""
    batch_entries = [
        {
            "title": "Batch Entry 1",
            "content": "First batch entry for testing bulk operations.",
            "entry_type": "text",
            "tags": ["batch", "test"]
        },
        {
            "title": "Batch Entry 2",
            "content": "Second batch entry with different content for testing.",
            "entry_type": "document",
            "tags": ["batch", "document"]
        },
        {
            "title": "Batch Entry 3",
            "content": "Third batch entry to test the batch creation limit.",
            "entry_type": "text",
            "tags": ["batch", "limit"]
        }
    ]
    
    try:
        response = client.post("/api/v1/feed/batch", json=batch_entries)
        success = response.status_code == 201
        if success:
            data = response.json()
            details = f"Created: {len(data)} entries"
        else:
            details = f"Status: {response.status_code}, Error: {response.text}"
        
        print_test_result("Batch Create Entries", success, details)
        return [entry['id'] for entry in data] if success else []
    except Exception as e:
        print_test_result("Batch Create Entries", False, f"Error: {str(e)}")
        return []

def test_batch_create_limit():
    """Test batch creation limit"""
    # Create more than 50 entries to test the limit
    batch_entries = []
    for i in range(51):
        batch_entries.append({
            "title": f"Limit Test Entry {i}",
            "content": f"Content for limit test entry {i}.",
            "entry_type": "text",
            "tags": ["limit", "test"]
        })
    
    try:
        response = client.post("/api/v1/feed/batch", json=batch_entries)
        success = response.status_code == 400  # Should fail due to limit
        if success:
            details = "Correctly rejected batch exceeding limit"
        else:
            details = f"Status: {response.status_code}, Expected: 400"
        
        print_test_result("Batch Create Limit Test", success, details)
    except Exception as e:
        print_test_result("Batch Create Limit Test", False, f"Error: {str(e)}")

def test_get_statistics():
    """Test getting feed statistics"""
    try:
        response = client.get("/api/v1/feed/stats/summary")
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"Active: {data['total_active_entries']}, Deleted: {data['total_deleted_entries']}, Total: {data['total_entries']}"
        else:
            details = f"Status: {response.status_code}, Error: {response.text}"
        
        print_test_result("Get Statistics", success, details)
    except Exception as e:
        print_test_result("Get Statistics", False, f"Error: {str(e)}")

def test_soft_delete(entry_ids: List[str]):
    """Test soft deleting feed entries"""
    for i, entry_id in enumerate(entry_ids[:2]):  # Soft delete first 2 entries
        try:
            response = client.delete(f"/api/v1/feed/{entry_id}?hard_delete=false")
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Soft deleted: {data['entry_id']}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            print_test_result(f"Soft Delete Entry {i+1}", success, details)
        except Exception as e:
            print_test_result(f"Soft Delete Entry {i+1}", False, f"Error: {str(e)}")

def test_hard_delete(entry_ids: List[str]):
    """Test hard deleting feed entries"""
    for i, entry_id in enumerate(entry_ids[2:4]):  # Hard delete next 2 entries
        try:
            response = client.delete(f"/api/v1/feed/{entry_id}?hard_delete=true")
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Hard deleted: {data['entry_id']}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            print_test_result(f"Hard Delete Entry {i+1}", success, details)
        except Exception as e:
            print_test_result(f"Hard Delete Entry {i+1}", False, f"Error: {str(e)}")

def test_error_cases():
    """Test various error cases"""
    error_tests = [
        {
            "name": "Get Non-existent Entry",
            "method": "GET",
            "url": "/api/v1/feed/non-existent-id",
            "expected_status": 404
        },
        {
            "name": "Update Non-existent Entry",
            "method": "PUT",
            "url": "/api/v1/feed/non-existent-id",
            "data": {"title": "Updated"},
            "expected_status": 404
        },
        {
            "name": "Delete Non-existent Entry",
            "method": "DELETE",
            "url": "/api/v1/feed/non-existent-id?hard_delete=false",
            "expected_status": 404
        },
        {
            "name": "Create Entry with Invalid Data",
            "method": "POST",
            "url": "/api/v1/feed/",
            "data": {"title": ""},  # Empty title should fail validation
            "expected_status": 422
        },
        {
            "name": "Create Entry with Missing Required Fields",
            "method": "POST",
            "url": "/api/v1/feed/",
            "data": {"title": "Test"},  # Missing content
            "expected_status": 422
        }
    ]
    
    for test in error_tests:
        try:
            if test["method"] == "GET":
                response = client.get(test["url"])
            elif test["method"] == "POST":
                response = client.post(test["url"], json=test["data"])
            elif test["method"] == "PUT":
                response = client.put(test["url"], json=test["data"])
            elif test["method"] == "DELETE":
                response = client.delete(test["url"])
            
            success = response.status_code == test["expected_status"]
            details = f"Status: {response.status_code}, Expected: {test['expected_status']}"
            
            print_test_result(test["name"], success, details)
        except Exception as e:
            print_test_result(test["name"], False, f"Error: {str(e)}")

def test_chat_integration():
    """Test chat integration with feed content"""
    chat_tests = [
        {
            "name": "Legacy Chat Endpoint",
            "url": "/chat",
            "data": {"message": "Tell me about testing procedures"}
        },
        {
            "name": "Enhanced Chat Endpoint",
            "url": "/api/v1/chat",
            "data": {"user_id": "test_user", "message": "What documentation do you have?"}
        }
    ]
    
    for test in chat_tests:
        try:
            response = client.post(test["url"], json=test["data"])
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Response received, Latency: {data.get('latency_ms', 'N/A')}ms"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            print_test_result(test["name"], success, details)
        except Exception as e:
            print_test_result(test["name"], False, f"Error: {str(e)}")

def test_legacy_endpoints():
    """Test legacy endpoints for backward compatibility"""
    legacy_tests = [
        {
            "name": "Legacy Feed List",
            "method": "GET",
            "url": "/feed"
        },
        {
            "name": "Legacy Feed Edit",
            "method": "PUT",
            "url": "/feed/edit",
            "data": {"id": "test-id", "new_content": "Updated content"}
        },
        {
            "name": "Legacy Feed Delete",
            "method": "DELETE",
            "url": "/feed/delete/test-id"
        }
    ]
    
    for test in legacy_tests:
        try:
            if test["method"] == "GET":
                response = client.get(test["url"])
            elif test["method"] == "PUT":
                response = client.put(test["url"], json=test["data"])
            elif test["method"] == "DELETE":
                response = client.delete(test["url"])
            
            success = response.status_code in [200, 404]  # Both success and not found are acceptable
            details = f"Status: {response.status_code}"
            
            print_test_result(test["name"], success, details)
        except Exception as e:
            print_test_result(test["name"], False, f"Error: {str(e)}")

def test_validation_scenarios():
    """Test various validation scenarios"""
    validation_tests = [
        {
            "name": "Title Too Long",
            "data": {"title": "A" * 201, "content": "Valid content"},
            "expected_status": 422
        },
        {
            "name": "Empty Content",
            "data": {"title": "Valid Title", "content": ""},
            "expected_status": 422
        },
        {
            "name": "Invalid Entry Type",
            "data": {"title": "Valid Title", "content": "Valid content", "entry_type": "invalid_type"},
            "expected_status": 422
        },
        {
            "name": "Valid Minimal Entry",
            "data": {"title": "Valid Title", "content": "Valid content"},
            "expected_status": 201
        }
    ]
    
    for test in validation_tests:
        try:
            response = client.post("/api/v1/feed/", json=test["data"])
            success = response.status_code == test["expected_status"]
            details = f"Status: {response.status_code}, Expected: {test['expected_status']}"
            
            print_test_result(test["name"], success, details)
        except Exception as e:
            print_test_result(test["name"], False, f"Error: {str(e)}")

def main():
    """Main test function"""
    print("🧪 Comprehensive Internal Feed Management System Test")
    print("=" * 70)
    print()
    
    # Test health endpoint first
    if not test_health_endpoint():
        print("❌ Health check failed. Application may not be working correctly.")
        return
    
    print("📝 Testing Feed Entry Creation...")
    created_entries = test_create_feed_entries()
    entry_ids = [entry['id'] for entry in created_entries]
    
    if not entry_ids:
        print("❌ No entries created. Stopping tests.")
        return
    
    print("📖 Testing Feed Entry Retrieval...")
    test_get_feed_entries(entry_ids)
    
    print("✏️ Testing Feed Entry Updates...")
    test_update_feed_entries(entry_ids)
    
    print("📋 Testing Feed Entry Listing...")
    test_list_feed_entries()
    
    print("🔍 Testing Feed Entry Search...")
    test_search_feed_entries()
    
    print("🧩 Testing Chunk Retrieval...")
    test_get_chunks(entry_ids)
    
    print("📦 Testing Batch Operations...")
    batch_ids = test_batch_create()
    test_batch_create_limit()
    
    print("📊 Testing Statistics...")
    test_get_statistics()
    
    print("🗑️ Testing Deletion Operations...")
    test_soft_delete(entry_ids)
    test_hard_delete(entry_ids)
    
    print("⚠️ Testing Error Cases...")
    test_error_cases()
    
    print("💬 Testing Chat Integration...")
    test_chat_integration()
    
    print("🔄 Testing Legacy Endpoints...")
    test_legacy_endpoints()
    
    print("✅ Testing Validation Scenarios...")
    test_validation_scenarios()
    
    print("🎉 Comprehensive Internal Testing Complete!")
    print("=" * 70)
    print("All internal tests have been executed using FastAPI TestClient.")
    print("This verifies the complete functionality without needing a running server.")

if __name__ == "__main__":
    main() 