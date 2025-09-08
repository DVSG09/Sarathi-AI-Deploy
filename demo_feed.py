#!/usr/bin/env python3
"""
Demo script for Sarathi Feed Management System

This script demonstrates the key features of the feed management system:
- Creating feed entries
- Searching content
- Updating entries
- Deleting entries
- Batch operations
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/feed"

def print_response(title: str, response: requests.Response):
    """Pretty print API responses"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status: {response.status_code}")
    if response.status_code < 400:
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
        except:
            print(response.text)
    else:
        print(f"Error: {response.text}")
    print(f"{'='*50}")

def create_sample_entries():
    """Create sample feed entries for demonstration"""
    
    entries = [
        {
            "title": "Product Documentation",
            "content": """
            Our product is a comprehensive customer support platform that helps businesses 
            manage customer inquiries efficiently. The platform includes features like 
            automated responses, ticket management, and analytics dashboard.
            
            Key Features:
            - Automated customer support
            - Ticket tracking and management
            - Real-time analytics
            - Multi-channel support (email, chat, phone)
            - Integration with popular CRM systems
            """,
            "entry_type": "document",
            "tags": ["product", "documentation", "features"],
            "metadata": {"author": "Product Team", "version": "1.0"}
        },
        {
            "title": "API Integration Guide",
            "content": """
            This guide explains how to integrate our API into your existing systems.
            
            Authentication:
            - Use API keys for authentication
            - Include key in Authorization header
            - Rate limiting: 1000 requests per hour
            
            Endpoints:
            - POST /api/v1/chat - Send chat messages
            - GET /api/v1/feed - List feed entries
            - POST /api/v1/feed - Create new entries
            
            Example Usage:
            curl -X POST "https://api.example.com/chat" \\
              -H "Authorization: Bearer YOUR_API_KEY" \\
              -H "Content-Type: application/json" \\
              -d '{"message": "Hello, I need help"}'
            """,
            "entry_type": "document",
            "tags": ["api", "integration", "technical"],
            "metadata": {"author": "Engineering Team", "version": "2.1"}
        },
        {
            "title": "Customer Support Best Practices",
            "content": """
            Effective customer support is crucial for business success. Here are some 
            best practices to follow:
            
            1. Respond Quickly: Aim to respond within 24 hours
            2. Be Empathetic: Understand and acknowledge customer concerns
            3. Provide Clear Solutions: Give actionable steps to resolve issues
            4. Follow Up: Check if the solution worked for the customer
            5. Document Everything: Keep records of all interactions
            
            Common Support Scenarios:
            - Product inquiries
            - Technical issues
            - Billing questions
            - Feature requests
            - Complaints and escalations
            """,
            "entry_type": "document",
            "tags": ["support", "best-practices", "customer-service"],
            "metadata": {"author": "Support Team", "version": "1.5"}
        }
    ]
    
    created_entries = []
    
    for entry in entries:
        response = requests.post(API_BASE, json=entry)
        print_response(f"Creating Entry: {entry['title']}", response)
        
        if response.status_code == 201:
            created_entries.append(response.json())
    
    return created_entries

def demonstrate_search():
    """Demonstrate search functionality"""
    
    # Search for technical content
    search_query = {
        "query": "API integration technical",
        "limit": 5
    }
    response = requests.post(f"{API_BASE}/search", json=search_query)
    print_response("Search: API Integration", response)
    
    # Search with tag filtering
    search_with_tags = {
        "query": "customer support",
        "limit": 5,
        "tags": ["support"]
    }
    response = requests.post(f"{API_BASE}/search", json=search_with_tags)
    print_response("Search: Customer Support with Tags", response)
    
    # Search for product features
    product_search = {
        "query": "features dashboard analytics",
        "limit": 3
    }
    response = requests.post(f"{API_BASE}/search", json=product_search)
    print_response("Search: Product Features", response)

def demonstrate_listing():
    """Demonstrate listing functionality"""
    
    # List all entries
    response = requests.get(f"{API_BASE}/")
    print_response("List All Entries", response)
    
    # List with pagination
    response = requests.get(f"{API_BASE}/?page=1&page_size=2")
    print_response("List Entries (Page 1, Size 2)", response)

def demonstrate_update(entry_id: str):
    """Demonstrate update functionality"""
    
    update_data = {
        "title": "Updated Product Documentation v2.0",
        "content": """
        Our product is a comprehensive customer support platform that helps businesses 
        manage customer inquiries efficiently. The platform includes advanced features like 
        AI-powered automated responses, intelligent ticket routing, real-time analytics 
        dashboard, and seamless CRM integrations.
        
        Enhanced Features:
        - AI-powered customer support automation
        - Intelligent ticket routing and prioritization
        - Advanced analytics and reporting
        - Multi-channel support (email, chat, phone, social media)
        - Deep integration with popular CRM systems
        - Custom workflow automation
        """,
        "tags": ["product", "documentation", "features", "ai", "updated"],
        "metadata": {"author": "Product Team", "version": "2.0", "updated_by": "demo_script"}
    }
    
    response = requests.put(f"{API_BASE}/{entry_id}", json=update_data)
    print_response(f"Update Entry: {entry_id}", response)

def demonstrate_chunks(entry_id: str):
    """Demonstrate chunk retrieval"""
    
    response = requests.get(f"{API_BASE}/{entry_id}/chunks")
    print_response(f"Get Chunks for Entry: {entry_id}", response)

def demonstrate_batch_operations():
    """Demonstrate batch creation"""
    
    batch_entries = [
        {
            "title": "Quick Start Guide",
            "content": "Get started with our platform in 5 minutes. Follow these simple steps to set up your account and start managing customer support.",
            "entry_type": "document",
            "tags": ["quick-start", "guide"],
            "metadata": {"author": "Onboarding Team"}
        },
        {
            "title": "Troubleshooting FAQ",
            "content": "Common issues and their solutions. This FAQ covers the most frequently encountered problems and how to resolve them quickly.",
            "entry_type": "document",
            "tags": ["faq", "troubleshooting", "support"],
            "metadata": {"author": "Support Team"}
        },
        {
            "title": "Security Best Practices",
            "content": "Learn about security best practices for protecting your data and ensuring compliance with industry standards.",
            "entry_type": "document",
            "tags": ["security", "compliance", "best-practices"],
            "metadata": {"author": "Security Team"}
        }
    ]
    
    response = requests.post(f"{API_BASE}/batch", json=batch_entries)
    print_response("Batch Create Entries", response)

def demonstrate_statistics():
    """Demonstrate statistics endpoint"""
    
    response = requests.get(f"{API_BASE}/stats/summary")
    print_response("Feed Statistics", response)

def demonstrate_deletion(entry_id: str):
    """Demonstrate deletion functionality"""
    
    # Soft delete
    response = requests.delete(f"{API_BASE}/{entry_id}", json={"hard_delete": False})
    print_response(f"Soft Delete Entry: {entry_id}", response)
    
    # Try to retrieve the deleted entry
    response = requests.get(f"{API_BASE}/{entry_id}")
    print_response(f"Get Deleted Entry (should fail): {entry_id}", response)

def main():
    """Main demonstration function"""
    
    print("🚀 Sarathi Feed Management System Demo")
    print("=" * 60)
    
    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("❌ Server is not responding properly")
            return
        print("✅ Server is running")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
        return
    
    # Step 1: Create sample entries
    print("\n📝 Step 1: Creating Sample Entries")
    created_entries = create_sample_entries()
    
    if not created_entries:
        print("❌ Failed to create entries. Stopping demo.")
        return
    
    # Step 2: Demonstrate search
    print("\n🔍 Step 2: Demonstrating Search Functionality")
    demonstrate_search()
    
    # Step 3: Demonstrate listing
    print("\n📋 Step 3: Demonstrating Listing Functionality")
    demonstrate_listing()
    
    # Step 4: Demonstrate update
    print("\n✏️  Step 4: Demonstrating Update Functionality")
    if created_entries:
        demonstrate_update(created_entries[0]["id"])
    
    # Step 5: Demonstrate chunks
    print("\n🧩 Step 5: Demonstrating Chunk Retrieval")
    if created_entries:
        demonstrate_chunks(created_entries[0]["id"])
    
    # Step 6: Demonstrate batch operations
    print("\n📦 Step 6: Demonstrating Batch Operations")
    demonstrate_batch_operations()
    
    # Step 7: Demonstrate statistics
    print("\n📊 Step 7: Demonstrating Statistics")
    demonstrate_statistics()
    
    # Step 8: Demonstrate deletion
    print("\n🗑️  Step 8: Demonstrating Deletion Functionality")
    if created_entries:
        demonstrate_deletion(created_entries[-1]["id"])
    
    print("\n🎉 Demo completed successfully!")
    print("\nYou can now:")
    print("- Visit http://localhost:8000/docs for interactive API documentation")
    print("- Use the web interface at http://localhost:8000")
    print("- Run the tests with: pytest tests/test_feed.py")

if __name__ == "__main__":
    main() 