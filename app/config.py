from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Sarathi")
    app_env: str = os.getenv("APP_ENV", "dev")
    log_level: str = os.getenv("LOG_LEVEL", "info")
    enabled_intents: set[str] = set(
        os.getenv("ENABLED_INTENTS", "status,faq,billing,appointment,account").split(",")
    )

settings = Settings()
