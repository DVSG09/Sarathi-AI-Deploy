#!/usr/bin/env python3
"""
Comprehensive Test Script for Sarathi Feed Management System

This script tests all possible scenarios and edge cases for the feed management API.
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/feed"

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
        response = requests.get(f"{BASE_URL}/health", timeout=5)
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
            response = requests.post(API_BASE, json=entry, timeout=10)
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
            response = requests.get(f"{API_BASE}/{entry_id}", timeout=5)
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
            response = requests.put(f"{API_BASE}/{entry_id}", json=update, timeout=10)
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
            response = requests.get(API_BASE, params=params, timeout=5)
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
            response = requests.post(f"{API_BASE}/search", json=query, timeout=10)
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
            response = requests.get(f"{API_BASE}/{entry_id}/chunks", timeout=5)
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
        response = requests.post(f"{API_BASE}/batch", json=batch_entries, timeout=15)
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
        response = requests.post(f"{API_BASE}/batch", json=batch_entries, timeout=15)
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
        response = requests.get(f"{API_BASE}/stats/summary", timeout=5)
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
            response = requests.delete(f"{API_BASE}/{entry_id}?hard_delete=false", timeout=5)
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
            response = requests.delete(f"{API_BASE}/{entry_id}?hard_delete=true", timeout=5)
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
            "url": f"{API_BASE}/non-existent-id",
            "expected_status": 404
        },
        {
            "name": "Update Non-existent Entry",
            "method": "PUT",
            "url": f"{API_BASE}/non-existent-id",
            "data": {"title": "Updated"},
            "expected_status": 404
        },
        {
            "name": "Delete Non-existent Entry",
            "method": "DELETE",
            "url": f"{API_BASE}/non-existent-id?hard_delete=false",
            "expected_status": 404
        },
        {
            "name": "Create Entry with Invalid Data",
            "method": "POST",
            "url": API_BASE,
            "data": {"title": ""},  # Empty title should fail validation
            "expected_status": 422
        },
        {
            "name": "Create Entry with Missing Required Fields",
            "method": "POST",
            "url": API_BASE,
            "data": {"title": "Test"},  # Missing content
            "expected_status": 422
        }
    ]
    
    for test in error_tests:
        try:
            if test["method"] == "GET":
                response = requests.get(test["url"], timeout=5)
            elif test["method"] == "POST":
                response = requests.post(test["url"], json=test["data"], timeout=5)
            elif test["method"] == "PUT":
                response = requests.put(test["url"], json=test["data"], timeout=5)
            elif test["method"] == "DELETE":
                response = requests.delete(test["url"], timeout=5)
            
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
            "url": f"{BASE_URL}/chat",
            "data": {"message": "Tell me about testing procedures"}
        },
        {
            "name": "Enhanced Chat Endpoint",
            "url": f"{BASE_URL}/api/v1/chat",
            "data": {"user_id": "test_user", "message": "What documentation do you have?"}
        }
    ]
    
    for test in chat_tests:
        try:
            response = requests.post(test["url"], json=test["data"], timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                details = f"Response received, Latency: {data.get('latency_ms', 'N/A')}ms"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            
            print_test_result(test["name"], success, details)
        except Exception as e:
            print_test_result(test["name"], False, f"Error: {str(e)}")

def main():
    """Main test function"""
    print("🧪 Comprehensive Feed Management System Test")
    print("=" * 60)
    print()
    
    # Test health endpoint first
    if not test_health_endpoint():
        print("❌ Health check failed. Server may not be running.")
        print("Please start the server with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
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
    
    print("🎉 Comprehensive Testing Complete!")
    print("=" * 60)
    print("All tests have been executed. Check the results above for any failures.")

if __name__ == "__main__":
    main() 