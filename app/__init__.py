import secrets
from pathlib import Path

from flask import Flask, session

from app.config import Config
from app.controllers.auth import auth
from app.controllers.notes import notes
from app.models.database import UserDatabase


def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    @app.context_processor
    def security_context():
        token = session.get("csrf_token")
        if token is None:
            token = secrets.token_urlsafe(32)
            session["csrf_token"] = token
        return {"csrf_token": token}

    @app.before_request
    def protect_state_changes():
        from flask import request

        if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            return
        expected = session.get("csrf_token")
        submitted = request.form.get("csrf_token") or request.headers.get(
            "X-CSRF-Token"
        )
        if not expected or not submitted or not secrets.compare_digest(
            expected, submitted
        ):
            from flask import abort

            abort(400, description="Invalid or missing CSRF token.")
        return

    Path(app.config["DOCUMENT_ROOT"]).mkdir(parents=True, exist_ok=True)
    user_database = UserDatabase(
        app.config["DATABASE_PATH"], app.config["SECRET_KEY"]
    )
    user_database.initialize()
    if (
        app.config["ADMIN_PASSWORD"]
        and user_database.find_by_username(app.config["ADMIN_USERNAME"]) is None
    ):
        user_database.create_user(
            app.config["ADMIN_USERNAME"], app.config["ADMIN_PASSWORD"], "admin"
        )
    if app.config["DEMO_PASSWORD"]:
        for username in app.config["DEMO_USERNAMES"]:
            if user_database.find_by_username(username) is None:
                user_database.create_user(username, app.config["DEMO_PASSWORD"])
    app.register_blueprint(auth)
    app.register_blueprint(notes)
    return app


app = create_app()
