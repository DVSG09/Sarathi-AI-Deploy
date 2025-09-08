# Sarathi Chatbot with Enhanced Feed Management

A FastAPI-based chatbot system with comprehensive feed management capabilities, including vector embeddings, semantic search, and content chunking.

## Features

### Core Chatbot Features
- **Intent-based routing** for different types of user queries
- **Knowledge base integration** with semantic search
- **Tool integration** for order status, appointments, billing, and account management
- **Telemetry and monitoring** with response latency tracking

### Enhanced Feed Management Features
- **Feed Injection**: Create new feed entries with automatic content chunking and vector embeddings
- **Content Modification**: Update existing entries with automatic re-indexing
- **Content Deletion**: Soft and hard delete options with proper cleanup
- **Semantic Search**: Vector-based similarity search using sentence transformers
- **Tag-based Filtering**: Organize and filter content by tags
- **Batch Operations**: Efficient bulk creation of feed entries
- **Pagination**: Scalable listing with configurable page sizes
- **Statistics**: Feed usage analytics and metrics

## Architecture

```
├── app/
│   ├── main.py              # Main FastAPI application
│   ├── config.py            # Configuration settings
│   ├── schemas.py           # Pydantic models and validation
│   ├── router_chat.py       # Chat API endpoints
│   ├── router_feed.py       # Feed management API endpoints
│   └── services/
│       ├── agent.py         # Chat intent routing and handling
│       ├── database.py      # SQLite database operations
│       ├── embeddings.py    # Vector embeddings and chunking
│       ├── feed.py          # Feed management orchestration
│       ├── kb.py            # Knowledge base operations
│       ├── telemetry.py     # Performance monitoring
│       └── tools.py         # External service integrations
├── tests/
│   ├── test_chat.py         # Chat functionality tests
│   └── test_feed.py         # Feed management tests
└── static/
    └── index.html           # Frontend interface
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sarathi-backend/sarathi
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Access the application**
   - Web interface: http://localhost:8000
   - API documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## API Documentation

### Feed Management Endpoints

#### 1. Create Feed Entry
```http
POST /api/v1/feed/
Content-Type: application/json

{
  "title": "Product Documentation",
  "content": "This is the content of the feed entry...",
  "source": "https://example.com/doc",
  "entry_type": "document",
  "tags": ["documentation", "product"],
  "metadata": {
    "author": "John Doe",
    "version": "1.0"
  }
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "title": "Product Documentation",
  "content": "This is the content of the feed entry...",
  "source": "https://example.com/doc",
  "entry_type": "document",
  "tags": ["documentation", "product"],
  "metadata": {"author": "John Doe", "version": "1.0"},
  "status": "active",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00",
  "chunks_count": 3
}
```

#### 2. Get Feed Entry
```http
GET /api/v1/feed/{entry_id}
```

#### 3. Update Feed Entry
```http
PUT /api/v1/feed/{entry_id}
Content-Type: application/json

{
  "title": "Updated Product Documentation",
  "content": "Updated content...",
  "tags": ["documentation", "product", "updated"]
}
```

#### 4. Delete Feed Entry
```http
DELETE /api/v1/feed/{entry_id}
Content-Type: application/json

{
  "hard_delete": false
}
```

#### 5. List Feed Entries
```http
GET /api/v1/feed/?page=1&page_size=10&status=active
```

#### 6. Search Feed Entries
```http
POST /api/v1/feed/search
Content-Type: application/json

{
  "query": "product documentation",
  "limit": 10,
  "tags": ["documentation"]
}
```

#### 7. Get Entry Chunks
```http
GET /api/v1/feed/{entry_id}/chunks
```

#### 8. Batch Create Entries
```http
POST /api/v1/feed/batch
Content-Type: application/json

[
  {
    "title": "Entry 1",
    "content": "Content 1..."
  },
  {
    "title": "Entry 2", 
    "content": "Content 2..."
  }
]
```

#### 9. Get Feed Statistics
```http
GET /api/v1/feed/stats/summary
```

### Chat Endpoints

#### Legacy Chat (Backward Compatible)
```http
POST /chat
Content-Type: application/json

{
  "message": "Where is my order?"
}
```

#### Enhanced Chat
```http
POST /api/v1/chat
Content-Type: application/json

{
  "user_id": "user_123",
  "message": "Where is my order ORD123?"
}
```

## Usage Examples

### Python Client Example

```python
import requests

# Create a feed entry
entry_data = {
    "title": "API Documentation",
    "content": "This document explains how to use our REST API...",
    "entry_type": "document",
    "tags": ["api", "documentation"],
    "metadata": {"version": "1.0"}
}

response = requests.post("http://localhost:8000/api/v1/feed/", json=entry_data)
entry_id = response.json()["id"]

# Search for content
search_data = {
    "query": "REST API usage",
    "limit": 5
}
results = requests.post("http://localhost:8000/api/v1/feed/search", json=search_data)

# Update entry
update_data = {
    "title": "Updated API Documentation",
    "content": "Updated content with new examples..."
}
requests.put(f"http://localhost:8000/api/v1/feed/{entry_id}", json=update_data)

# Delete entry (soft delete)
requests.delete(f"http://localhost:8000/api/v1/feed/{entry_id}", 
                json={"hard_delete": False})
```

### cURL Examples

```bash
# Create entry
curl -X POST "http://localhost:8000/api/v1/feed/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Entry",
    "content": "This is a test entry for the feed system."
  }'

# Search entries
curl -X POST "http://localhost:8000/api/v1/feed/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test entry",
    "limit": 10
  }'

# List entries
curl "http://localhost:8000/api/v1/feed/?page=1&page_size=5"
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
APP_NAME=Sarathi
APP_ENV=dev
LOG_LEVEL=info
ENABLED_INTENTS=status,faq,billing,appointment,account
```

### Database Configuration

The system uses SQLite by default. The database file (`sarathi_feed.db`) is created automatically in the project root.

### Embedding Model

The system uses the `all-MiniLM-L6-v2` model from sentence-transformers for generating embeddings. This model provides a good balance between performance and accuracy.

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_feed.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app tests/
```

## Key Features Explained

### 1. Content Chunking
- Automatically splits long content into overlapping chunks
- Preserves context across chunk boundaries
- Configurable chunk size and overlap

### 2. Vector Embeddings
- Uses sentence-transformers for semantic understanding
- Enables similarity-based search
- Supports multiple languages

### 3. Soft vs Hard Delete
- **Soft Delete**: Marks entries as deleted but preserves data
- **Hard Delete**: Permanently removes entries and associated chunks
- Default behavior is soft delete for data safety

### 4. Tag-based Organization
- Flexible tagging system for content categorization
- Tag-based filtering in search operations
- Supports multiple tags per entry

### 5. Batch Operations
- Efficient bulk creation of feed entries
- Configurable batch size limits
- Error handling for individual entry failures

## Performance Considerations

### Database Optimization
- Indexed fields for faster queries
- Efficient JSON storage for metadata and tags
- Connection pooling for better resource management

### Embedding Processing
- Batch processing for multiple entries
- Caching of embeddings for repeated queries
- Configurable model selection for different use cases

### Search Performance
- Hybrid search combining text matching and semantic similarity
- Configurable result limits
- Efficient chunk-based similarity calculations

## Error Handling

The API provides comprehensive error handling:

- **400 Bad Request**: Invalid input data or validation errors
- **404 Not Found**: Requested resource doesn't exist
- **500 Internal Server Error**: Server-side processing errors

All errors include descriptive messages and appropriate HTTP status codes.

## Monitoring and Logging

- Request/response logging
- Performance metrics (latency tracking)
- Error tracking and reporting
- Feed operation statistics

## Future Enhancements

- **Multi-language Support**: Enhanced language detection and processing
- **Advanced Search**: Faceted search, date range filtering
- **Content Versioning**: Track changes and maintain history
- **Access Control**: User-based permissions and access management
- **Real-time Updates**: WebSocket support for live feed updates
- **Export/Import**: Bulk data operations and backup functionality

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
