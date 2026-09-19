import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Meta / Facebook Settings
    PAGE_ACCESS_TOKEN: str = "placeholder_token"
    VERIFY_TOKEN: str = "my_super_secret_verify_token"
    PAGE_ID: Optional[str] = None
    GRAPH_API_VERSION: str = "v21.0"

    # Gemini AI
    GEMINI_API_KEY: Optional[str] = None

    # Google Sheets
    GOOGLE_CREDS_FILE: str = "service_account.json"
    GOOGLE_SHEET_ID: Optional[str] = None
    SHEET_PRODUCTS_TAB: str = "Products"
    SHEET_ORDERS_TAB: str = "Orders"

    # Server
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
