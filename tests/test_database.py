from app.models.database import UserDatabase
from flask import g
from app.controllers.notes import _store
from app.models.documents import DocumentStore
from app import app

def test_create_user_and_authenticate(tmp_path):
    # Arrange
    database = UserDatabase(
        tmp_path / "users.sqlite3",
        "test-secret-key",
    )
    database.initialize()

    username = "alice"
    password = "StrongPassword1!"

    # Act
    user_id = database.create_user(username, password)
    user = database.authenticate(username, password)

    # Assert
    assert user_id == 1
    assert user is not None
    assert user["id"] == user_id
    assert user["role"] == "user"
    assert database.authenticate(username, "wrong-password") is None

def test_home_page():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_store_returns_document_store(app, tmp_path):
    app.config["DOCUMENT_ROOT"] = tmp_path
    app.config["SUPPORTED_DOCUMENT_EXTENSIONS"] = {".md"}
    app.config["EXCLUDED_DOCUMENT_NAMES"] = set()

    with app.test_request_context():
        g.user = {"id": 123}

        store = _store()

        assert isinstance(store, DocumentStore)

        notebook_path = tmp_path / "notebooks" / "123"
        assert notebook_path.exists()
        assert notebook_path.is_dir()