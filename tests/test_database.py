from app.models.database import UserDatabase


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

from app import app

def test_home_page():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

