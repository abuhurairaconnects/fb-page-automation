import os
from pydantic_settings import BaseSettings
from typing import Optional

LATEST_PAGE_ACCESS_TOKEN = "EAAf6mwlHtLUBSht26sVrSGXohhZBK4fVh5YNpA5ZAIAmYZCdrr7mNAgIIaeRDSUdrgV41MKWd0PInpjVhoPipXhBzT0A6j4iAZBfS5OrDS2zK47LRcWg1mSkmRe0TZAbSgtpyvax5T8X5ytxhCUu71f9ezE6yYgYIMkciNdsI6ypqTOd1I4XwiG25tZAWw5oSRImAwV39ch3SZCxCYuGUfobVQVGSu6ZB7OfU5r0CaimDo4ZD"

class Settings(BaseSettings):
    # Meta / Facebook Settings
    PAGE_ACCESS_TOKEN: str = LATEST_PAGE_ACCESS_TOKEN
    VERIFY_TOKEN: str = "raw_fabric_secret_token_786"
    PAGE_ID: Optional[str] = "1304777106056536"
    GRAPH_API_VERSION: str = "v21.0"

    # Gemini AI
    GEMINI_API_KEY: Optional[str] = None

    # Google Sheets
    GOOGLE_CREDS_FILE: str = "service_account.json"
    GOOGLE_SHEET_ID: Optional[str] = "1m3BaNq8mWi0DmwbMHefJ_uPoPXWIlX9zxNQwxxSnf7k"
    SHEET_PRODUCTS_TAB: str = "Sheet1"
    SHEET_ORDERS_TAB: str = "Orders"

    # Server
    PORT: int = 5678
    HOST: str = "0.0.0.0"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Automatically ensure the latest valid Page token is used even if old token is in Render dashboard
if not settings.PAGE_ACCESS_TOKEN or settings.PAGE_ACCESS_TOKEN.endswith("bT7kZD") or settings.PAGE_ACCESS_TOKEN == "placeholder_token":
    settings.PAGE_ACCESS_TOKEN = LATEST_PAGE_ACCESS_TOKEN
