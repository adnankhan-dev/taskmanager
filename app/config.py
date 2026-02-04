import os
from pydantic import BaseModel

def _env(key: str, default: str) -> str:
    value = os.getenv(key)
    return value if value is not None and value != "" else default

class Settings(BaseModel):
    app_name: str = _env("APP_NAME", "Task Management System v2")
    secret_key: str = _env("SECRET_KEY", "CHANGE_THIS_TO_A_LONG_RANDOM_STRING")
    session_cookie: str = _env("SESSION_COOKIE", "taskmgr_session")
    admin_username: str = _env("ADMIN_USERNAME", "admin")
    admin_password: str = _env("ADMIN_PASSWORD", "admin123")

settings = Settings()
