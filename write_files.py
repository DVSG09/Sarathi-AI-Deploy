
# write_files.py — populates your Sarathi project files
import os, textwrap

files = {
  ".gitignore": """
__pycache__/
*.pyc
.env
.venv/
dist/
*.log
.cache/
""",

  "requirements.txt": """
fastapi==0.115.5
uvicorn[standard]==0.30.6
pydantic==2.8.2
python-dotenv==1.0.1
httpx==0.27.2
pytest==8.3.2
pytest-asyncio==0.23.8
""",

  ".env.example": """
APP_NAME=Sarathi
APP_ENV=dev
LOG_LEVEL=info
# Comma-separated intents to enable (for demo toggles)
ENABLED_INTENTS=status,faq,billing,appointment,account
""",

  "README.md": """
# Sarathi (MVP)

FastAPI service for agentic customer support (demo).
Endpoints:
- `GET /health`
- `POST /api/v1/chat` → `{ user_id, message }`

## Run locally
```bash
copy .env.example .env
py -m venv .venv
.\\.venv\\Scripts\\activate.bat
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
