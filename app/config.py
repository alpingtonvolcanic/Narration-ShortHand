import os
from pathlib import Path
from typing import ClassVar


class Config:
    APP_NAME = "Narrator-Shorthand"
    SECRET_KEY = os.environ.get("SECRET_KEY", "local-development-key")
    DOCUMENT_ROOT = Path(
        os.environ.get("DOCUMENT_ROOT", Path.cwd())
    ).resolve()
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
