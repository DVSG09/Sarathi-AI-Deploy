from fastapi import FastAPI
from .router_chat import router
from .config import settings

app = FastAPI(title=settings.app_name)

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.app_env}

app.include_router(router)
