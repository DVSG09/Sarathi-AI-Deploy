<<<<<<< HEAD
# Sarathi-ai
=======
# Sarathi (MVP)

FastAPI service for agentic customer support (demo).  
Endpoints:

- `GET /health`
- `POST /api/v1/chat` → `{ user_id, message }`

## Run locally

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
>>>>>>> 5f789db (feat: Sarathi MVP backend (FastAPI + tests))
