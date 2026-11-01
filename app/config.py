import os
import secrets
from pathlib import Path
from typing import ClassVar


class Config:
    APP_NAME = "Narrator-Shorthand"
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "").lower() == "true"
    DOCUMENT_ROOT = Path(
        os.environ.get("DOCUMENT_ROOT", Path.cwd())
    ).resolve()
    DATABASE_PATH = Path(
        os.environ.get("DATABASE_PATH", DOCUMENT_ROOT / "users.sqlite3")
    ).resolve()
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "administrator")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
    DEMO_USERNAMES = ("demo1", "demo2")
    DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD")
    DEFAULT_DOCUMENT = "narratornotes1.doc"
    EXCLUDED_DOCUMENT_NAMES: ClassVar[set[str]] = {
        "readme.md",
        "requirements.txt",
        "assignment-information.txt",
    }
    SUPPORTED_DOCUMENT_EXTENSIONS: ClassVar[set[str]] = {
        ".adoc",
        ".doc",
        ".log",
        ".md",
        ".rst",
        ".text",
        ".txt",
    }
