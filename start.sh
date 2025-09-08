#!/bin/bash

# Sarathi Chatbot with Enhanced Feed Management - Startup Script

echo "🚀 Starting Sarathi Chatbot with Enhanced Feed Management..."

# Set required environment variables
export KMP_DUPLICATE_LIB_OK=TRUE

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Start the application
echo "🌟 Starting FastAPI server..."
echo "📖 API Documentation will be available at: http://localhost:8000/docs"
echo "🌐 Web interface will be available at: http://localhost:8000"
echo "💚 Health check will be available at: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 