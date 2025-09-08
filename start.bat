@echo off

REM Sarathi Chatbot with Enhanced Feed Management - Startup Script

echo 🚀 Starting Sarathi Chatbot with Enhanced Feed Management...

REM Set required environment variables
set KMP_DUPLICATE_LIB_OK=TRUE

REM Check if virtual environment exists
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Start the application
echo 🌟 Starting FastAPI server...
echo 📖 API Documentation will be available at: http://localhost:8000/docs
echo 🌐 Web interface will be available at: http://localhost:8000
echo 💚 Health check will be available at: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000