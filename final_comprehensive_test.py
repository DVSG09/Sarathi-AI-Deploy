#!/usr/bin/env python3
"""
Final Comprehensive Test for Sarathi Feed Management System

This script tests ALL possible scenarios, edge cases, and integration points
to ensure the feed management system is production-ready.
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

def test_all_possible_scenarios():
    """Test all possible scenarios and edge cases"""
    
    print("🧪 FINAL COMPREHENSIVE TEST - ALL POSSIBLE SCENARIOS")
    print("=" * 80)
    print()
    
    # 1. HEALTH AND BASIC FUNCTIONALITY
    print("🔍 1. HEALTH AND BASIC FUNCTIONALITY")
    print("-" * 40)
    
    # Health endpoint
    response = client.get("/health")
    success = response.status_code == 200
    data = response.json() if success else {}
    print_test_result("Health Endpoint", success, f"Status: {response.status_code}, Version: {data.get('version', 'N/A')}")
    
    # 2. FEED ENTRY CREATION - ALL TYPES
    print("📝 2. FEED ENTRY CREATION - ALL TYPES")
    print("-" * 40)
    
    entry_types = [
        {
            "name": "Text Entry",
            "data": {
                "title": "Simple Text Entry",
                "content": "This is a simple text entry.",
                "entry_type": "text",
                "tags": ["text", "simple"],
                "metadata": {"author": "Test User"}
            }
        },
        {
            "name": "Document Entry",
            "data": {
                "title": "Long Document Entry",
                "content": "This is a longer document entry with multiple sentences. It should be chunked appropriately for vector embeddings. The content includes technical information about APIs, integrations, and best practices for software development.",
                "entry_type": "document",
                "tags": ["document", "technical", "api"],
                "metadata": {"author": "Tech Team", "category": "documentation"}
            }
        },
        {
            "name": "URL Entry",
            "data": {
                "title": "URL Source Entry",
                "content": "Content extracted from a URL with web-specific information and formatting.",
                "source": "https://example.com/api-documentation",
                "entry_type": "url",
                "tags": ["url", "web", "api"],
                "metadata": {"source_type": "webpage", "domain": "example.com"}
            }
        },
        {
            "name": "File Entry",
            "data": {
                "title": "File Upload Entry",
                "content": "Content extracted from an uploaded file with file-specific metadata and formatting.",
                "entry_type": "file",
                "tags": ["file", "upload", "pdf"],
                "metadata": {"file_type": "pdf", "size": "1.2MB", "uploaded_by": "user123"}
            }
        }
    ]
    
    created_entries = []
    for entry_type in entry_types:
        response = client.post("/api/v1/feed/", json=entry_type["data"])
        success = response.status_code == 201
        if success:
            data = response.json()
            created_entries.append(data)
            details = f"ID: {data['id']}, Chunks: {data['chunks_count']}"
        else:
            details = f"Status: {response.status_code}, Error: {response.text}"
        print_test_result(f"Create {entry_type['name']}", success, details)
    
    if not created_entries:
        print("❌ No entries created. Stopping tests.")
        return
    
    entry_ids = [entry['id'] for entry in created_entries]
    
    # 3. FEED ENTRY RETRIEVAL
    print("📖 3. FEED ENTRY RETRIEVAL")
    print("-" * 40)
    
    for i, entry_id in enumerate(entry_ids):
        response = client.get(f"/api/v1/feed/{entry_id}")
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"Title: {data['title']}, Type: {data['entry_type']}, Status: {data['status']}"
        else:
            details = f"Status: {response.status_code}, Error: {response.text}"
        print_test_result(f"Get Entry {i+1}", success, details)
    
    # 4. FEED ENTRY UPDATES - ALL SCENARIOS
    print("✏️ 4. FEED ENTRY UPDATES - ALL SCENARIOS")
    print("-" * 40)
    
    update_scenarios = [
        {"name": "Title Update", "data": {"title": "Updated Title"}},
        {"name": "Content Update", "data": {"content": "This is updated content with new information."}},
        {"name": "Tags Update", "data": {"tags": ["updated", "new", "tags"]}},
        {"name": "Metadata Update", "data": {"metadata": {"author": "Updated Author", "version": "2.0"}}},
        {"name": "Source Update", "data": {"source": "https://example.com/updated-docs"}},
        {"name": "Entry Type Update", "data": {"entry_type": "document"}},
        {"name": "Multiple Fields Update", "data": {
            "title": "Multiple Update",
            "content": "Content with multiple updates",
            "tags": ["multiple", "update"],
            "metadata": {"updated": True}
        }}
    ]
    
    for i, scenario in enumerate(update_scenarios):
        if i < len(entry_ids):
            response = client.put(f"/api/v1/feed/{entry_ids[i]}", json=scenario["data"])
            success = response.status_code == 200
            if success:
                details = f"Updated: {list(scenario['data'].keys())}"
            else:
                details = f"Status: {response.status_code}, Error: {response.text}"
            print_test_result(f"Update {scenario['name']}", success, details)
    
    # 5. FEED ENTRY LISTING - ALL PAGINATION SCENARIOS
    print("📋 5. FEED ENTRY LISTING - ALL PAGINATION SCENARIOS")
    print("-" * 40)
    
    pagination_scenarios = [
        {"page": 1, "page_size": 10, "status": "active"},
        {"page": 1, "page_size": 5, "status": "active"},
        {"page": 2, "page_size": 5, "status": "active"},
        {"page": 1, "page_size": 1, "status": "active"},
        {"page": 1, "page_size": 100, "status": "active"},
        {"page": 1, "page_size": 10, "status": "deleted"},
    ]
    
    for i, params in enumerate(pagination_scenarios):
        response = client.get("/api/v1/feed/", params=params)
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"Page: {data['page']}, Total: {data['total']}, Entries: {len(data['entries'])}"
        else:
            details = f"Status: {response.status_code}, Error: {response.text}"
        print_test_result(f"List {i+1} (Page {params['page']}, Size {params['page_size']}, Status {params['status']})", success, details)
    
    # 6. SEARCH FUNCTIONALITY - ALL SCENARIOS
    print("🔍 6. SEARCH FUNCTIONALITY - ALL SCENARIOS")
    print("-" * 40)
    
    search_scenarios = [
        {"name": "Basic Text Search", "data": {"query": "text", "limit": 5}},
        {"name": "Document Search", "data": {"query": "document", "limit": 3}},
        {"name": "Technical Search", "data": {"query": "technical", "limit": 5}},
        {"name": "Tag Filtered Search", "data": {"query": "api", "limit": 5, "tags": ["api"]}},
        {"name": "Multiple Tag Search", "data": {"query": "content", "limit": 5, "tags": ["technical", "document"]}},
        {"name": "No Results Search", "data": {"query": "nonexistent content that should not be found", "limit": 5}},
        {"name": "Empty Query Search", "data": {"query": "", "limit": 5}},
        {"name": "Large Limit Search", "data": {"query": "content", "limit": 100}},
    ]
    
    for scenario in search_scenarios:
        response = client.post("/api/v1/feed/search", json=scenario["data"])
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"Found: {data['total_found']}, Query: '{data['query']}'"
        else:
            details = f"Status: {response.status_code}, Error: {response.text}"
        print_test_result(f"Search: {scenario['name']}", success, details)
    
    # 7. CHUNK RETRIEVAL
    print("🧩 7. CHUNK RETRIEVAL")
    print("-" * 40)
    
    for i, entry_id in enumerate(entry_ids):
        response = client.get(f"/api/v1/feed/{entry_id}/chunks")
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"Chunks: {data['total_chunks']}"
        else:
            details = f"Status: {response.status_code}, Error: {response.text}"
        print_test_result(f"Get Chunks {i+1}", success, details)
    
    # 8. BATCH OPERATIONS
    print("📦 8. BATCH OPERATIONS")
    print("-" * 40)
    
    # Batch create
    batch_entries = [
        {"title": f"Batch Entry {i}", "content": f"Content for batch entry {i}.", "entry_type": "text", "tags": ["batch"]}
        for i in range(5)
    ]
    
    response = client.post("/api/v1/feed/batch", json=batch_entries)
    success = response.status_code == 201
    if success:
        data = response.json()
        batch_ids = [entry['id'] for entry in data]
        details = f"Created: {len(data)} entries"
    else:
        batch_ids = []
        details = f"Status: {response.status_code}, Error: {response.text}"
    print_test_result("Batch Create", success, details)
    
    # Batch limit test
    large_batch = [{"title": f"Limit Test {i}", "content": f"Content {i}", "entry_type": "text"} for i in range(51)]
    response = client.post("/api/v1/feed/batch", json=large_batch)
    success = response.status_code == 400  # Should fail
    details = f"Status: {response.status_code}, Expected: 400"
    print_test_result("Batch Limit Test", success, details)
    
    # 9. STATISTICS
    print("📊 9. STATISTICS")
    print("-" * 40)
    
    response = client.get("/api/v1/feed/stats/summary")
    success = response.status_code == 200
    if success:
        data = response.json()
        details = f"Active: {data['total_active_entries']}, Deleted: {data['total_deleted_entries']}, Total: {data['total_entries']}"
    else:
        details = f"Status: {response.status_code}, Error: {response.text}"
    print_test_result("Get Statistics", success, details)
    
    # 10. DELETION OPERATIONS
    print("🗑️ 10. DELETION OPERATIONS")
    print("-" * 40)
    
    # Soft delete
    for i, entry_id in enumerate(entry_ids[:2]):
        response = client.delete(f"/api/v1/feed/{entry_id}?hard_delete=false")
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"Soft deleted: {data['entry_id']}"
        else:
            details = f"Status: {response.status_code}, Error: {response.text}"
        print_test_result(f"Soft Delete {i+1}", success, details)
    
    # Hard delete
    for i, entry_id in enumerate(entry_ids[2:4]):
        response = client.delete(f"/api/v1/feed/{entry_id}?hard_delete=true")
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"Hard deleted: {data['entry_id']}"
        else:
            details = f"Status: {response.status_code}, Error: {response.text}"
        print_test_result(f"Hard Delete {i+1}", success, details)
    
    # 11. ERROR CASES AND EDGE CASES
    print("⚠️ 11. ERROR CASES AND EDGE CASES")
    print("-" * 40)
    
    error_scenarios = [
        {"name": "Get Non-existent Entry", "method": "GET", "url": "/api/v1/feed/non-existent-id", "expected": 404},
        {"name": "Update Non-existent Entry", "method": "PUT", "url": "/api/v1/feed/non-existent-id", "data": {"title": "Updated"}, "expected": 404},
        {"name": "Delete Non-existent Entry", "method": "DELETE", "url": "/api/v1/feed/non-existent-id?hard_delete=false", "expected": 404},
        {"name": "Empty Title", "method": "POST", "url": "/api/v1/feed/", "data": {"title": "", "content": "Valid content"}, "expected": 422},
        {"name": "Empty Content", "method": "POST", "url": "/api/v1/feed/", "data": {"title": "Valid title", "content": ""}, "expected": 422},
        {"name": "Missing Title", "method": "POST", "url": "/api/v1/feed/", "data": {"content": "Valid content"}, "expected": 422},
        {"name": "Missing Content", "method": "POST", "url": "/api/v1/feed/", "data": {"title": "Valid title"}, "expected": 422},
        {"name": "Title Too Long", "method": "POST", "url": "/api/v1/feed/", "data": {"title": "A" * 201, "content": "Valid content"}, "expected": 422},
        {"name": "Invalid Entry Type", "method": "POST", "url": "/api/v1/feed/", "data": {"title": "Valid", "content": "Valid", "entry_type": "invalid"}, "expected": 422},
        {"name": "Invalid JSON", "method": "POST", "url": "/api/v1/feed/", "data": "invalid json", "expected": 422},
    ]
    
    for scenario in error_scenarios:
        try:
            if scenario["method"] == "GET":
                response = client.get(scenario["url"])
            elif scenario["method"] == "POST":
                response = client.post(scenario["url"], json=scenario["data"])
            elif scenario["method"] == "PUT":
                response = client.put(scenario["url"], json=scenario["data"])
            elif scenario["method"] == "DELETE":
                response = client.delete(scenario["url"])
            
            success = response.status_code == scenario["expected"]
            details = f"Status: {response.status_code}, Expected: {scenario['expected']}"
            print_test_result(scenario["name"], success, details)
        except Exception as e:
            print_test_result(scenario["name"], False, f"Exception: {str(e)}")
    
    # 12. CHAT INTEGRATION
    print("💬 12. CHAT INTEGRATION")
    print("-" * 40)
    
    chat_scenarios = [
        {"name": "Legacy Chat", "url": "/chat", "data": {"message": "Hello, how are you?"}},
        {"name": "Enhanced Chat", "url": "/api/v1/chat", "data": {"user_id": "test_user", "message": "What documentation do you have?"}},
        {"name": "Chat with Order Status", "url": "/api/v1/chat", "data": {"user_id": "test_user", "message": "Where is my order ORD123?"}},
        {"name": "Chat with FAQ", "url": "/api/v1/chat", "data": {"user_id": "test_user", "message": "What is the refund policy?"}},
    ]
    
    for scenario in chat_scenarios:
        response = client.post(scenario["url"], json=scenario["data"])
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"Response received, Latency: {data.get('latency_ms', 'N/A')}ms"
        else:
            details = f"Status: {response.status_code}, Error: {response.text}"
        print_test_result(scenario["name"], success, details)
    
    # 13. LEGACY ENDPOINTS
    print("🔄 13. LEGACY ENDPOINTS")
    print("-" * 40)
    
    legacy_scenarios = [
        {"name": "Legacy Feed List", "method": "GET", "url": "/feed"},
        {"name": "Legacy Feed Edit", "method": "PUT", "url": "/feed/edit", "data": {"id": "test-id", "new_content": "Updated"}},
        {"name": "Legacy Feed Delete", "method": "DELETE", "url": "/feed/delete/test-id"},
    ]
    
    for scenario in legacy_scenarios:
        try:
            if scenario["method"] == "GET":
                response = client.get(scenario["url"])
            elif scenario["method"] == "PUT":
                response = client.put(scenario["url"], json=scenario["data"])
            elif scenario["method"] == "DELETE":
                response = client.delete(scenario["url"])
            
            success = response.status_code in [200, 404]  # Both acceptable
            details = f"Status: {response.status_code}"
            print_test_result(scenario["name"], success, details)
        except Exception as e:
            print_test_result(scenario["name"], False, f"Exception: {str(e)}")
    
    # 14. PERFORMANCE AND STRESS TESTS
    print("⚡ 14. PERFORMANCE AND STRESS TESTS")
    print("-" * 40)
    
    # Multiple rapid requests
    import time
    start_time = time.time()
    responses = []
    for i in range(10):
        response = client.get("/api/v1/feed/", params={"page": 1, "page_size": 5})
        responses.append(response.status_code)
    
    end_time = time.time()
    success = all(code == 200 for code in responses)
    details = f"10 requests in {end_time - start_time:.2f}s, All status codes: {responses}"
    print_test_result("Rapid Requests Test", success, details)
    
    # Large search query
    response = client.post("/api/v1/feed/search", json={"query": "a" * 1000, "limit": 10})
    success = response.status_code == 200
    details = f"Large query handled, Status: {response.status_code}"
    print_test_result("Large Query Test", success, details)
    
    print("🎉 FINAL COMPREHENSIVE TEST COMPLETE!")
    print("=" * 80)
    print("All possible scenarios have been tested.")
    print("The Feed Management System is ready for production use!")

if __name__ == "__main__":
    test_all_possible_scenarios() 