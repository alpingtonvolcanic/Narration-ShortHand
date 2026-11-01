"""Application package and factory."""

from pathlib import Path

from flask import Flask

from app.config import Config
from app.controllers.notes import notes
from app.models.documents import DocumentStore


def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    Path(app.config["DOCUMENT_ROOT"]).mkdir(parents=True, exist_ok=True)
    DocumentStore(
        app.config["DOCUMENT_ROOT"],
        app.config["SUPPORTED_DOCUMENT_EXTENSIONS"],
        app.config["EXCLUDED_DOCUMENT_NAMES"],
    ).ensure_default_document(app.config["DEFAULT_DOCUMENT"])
    app.register_blueprint(notes)
    return app


app = create_app()
