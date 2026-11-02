import sqlite3
from contextlib import closing

from app import create_app


def post(client, path, data=None):
    with client.session_transaction() as session:
        token = session.setdefault("csrf_token", "test-csrf-token")
    data = dict(data or {})
    data["csrf_token"] = token
    return client.post(path, data=data)


def make_client(tmp_path, admin_password=None):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "DOCUMENT_ROOT": tmp_path,
            "DATABASE_PATH": tmp_path / "users.sqlite3",
            "ADMIN_PASSWORD": admin_password,
        }
    )
    client = app.test_client()
    post(
        client,
        "/signup",
        data={
            "username": "alice",
            "password": "StrongPassword1!",
            "password_confirmation": "StrongPassword1!",
        },
    )
    post(
        client,
        "/login",
        data={"username": "alice", "password": "StrongPassword1!"},
    )
    return client


def notebook_path(tmp_path):
    notebook = tmp_path / "notebooks" / "1" / "notebook.md"
    notebook.parent.mkdir(parents=True, exist_ok=True)
    return notebook


def test_signup_creates_private_notebook(tmp_path):
    client = make_client(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    assert notebook_path(tmp_path).exists()
    assert b"notebook.md" in response.data


def test_note_is_appended_and_last_update_is_stored(tmp_path):
    client = make_client(tmp_path)

    response = post(
        client,
        "/",
        data={"document": "notebook.md", "note": "CI is ready for review"},
    )

    assert response.status_code == 302
    assert "CI is ready for review" in notebook_path(tmp_path).read_text(
        encoding="utf-8"
    )
    with closing(
        sqlite3.connect(client.application.config["DATABASE_PATH"])
    ) as connection:
        last_update = connection.execute(
            "SELECT last_notebook_update FROM users WHERE id = 1"
        ).fetchone()[0]
    assert last_update is not None


def test_user_can_create_edit_and_delete_document_notes(tmp_path):
    client = make_client(tmp_path)

    response = post(client, "/documents", data={"filename": "ideas.md"})

    assert response.status_code == 302
    document = tmp_path / "notebooks" / "1" / "ideas.md"
    assert document.exists()

    post(client, "/", data={"document": "ideas.md", "note": "Initial idea"})
    assert client.get("/documents/ideas.md/notes").json["notes"][0]["text"] == (
        "Initial idea"
    )

    response = client.post(
        "/documents/ideas.md/notes/0",
        json={"text": "Updated idea"},
        headers={"X-CSRF-Token": "test-csrf-token"},
    )
    assert response.status_code == 200
    assert "Updated idea" in document.read_text(encoding="utf-8")

    response = client.delete(
        "/documents/ideas.md/notes/0",
        headers={"X-CSRF-Token": "test-csrf-token"},
    )
    assert response.status_code == 200
    assert document.read_text(encoding="utf-8") == ""


def test_user_can_delete_created_document_but_not_default_notebook(tmp_path):
    client = make_client(tmp_path)
    client.get("/")
    post(client, "/documents", data={"filename": "remove-me.md"})

    response = post(client, "/documents/remove-me.md/delete")

    assert response.status_code == 302
    assert not (tmp_path / "notebooks" / "1" / "remove-me.md").exists()

    response = post(client, "/documents/notebook.md/delete")

    assert response.status_code == 302
    assert (tmp_path / "notebooks" / "1" / "notebook.md").exists()


def test_document_contents_are_displayed(tmp_path):
    client = make_client(tmp_path)
    document = tmp_path / "notebooks" / "1" / "handoff.md"
    document.parent.mkdir(parents=True, exist_ok=True)
    document.write_text("Current sprint status", encoding="utf-8")

    response = client.get("/documents/handoff.md")

    assert response.status_code == 200
    assert response.json == {
        "filename": "handoff.md",
        "content": "Current sprint status",
    }


def test_invalid_document_path_is_rejected(tmp_path):
    client = make_client(tmp_path)
    document = notebook_path(tmp_path)
    document.write_text("unchanged\n", encoding="utf-8")

    response = post(client, "/", data={"document": "../notebook.md", "note": "bad"})

    assert response.status_code == 200
    assert document.read_text(encoding="utf-8") == "unchanged\n"


def test_users_have_separate_notebooks(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "DOCUMENT_ROOT": tmp_path,
            "DATABASE_PATH": tmp_path / "users.sqlite3",
        }
    )
    first = app.test_client()
    post(
        first,
        "/signup",
        data={
            "username": "alice",
            "password": "StrongPassword1!",
            "password_confirmation": "StrongPassword1!",
        },
    )
    post(first, "/login", data={"username": "alice", "password": "StrongPassword1!"})
    post(first, "/", data={"document": "notebook.md", "note": "private note"})

    second = app.test_client()
    post(
        second,
        "/signup",
        data={
            "username": "bob",
            "password": "StrongPassword2!",
            "password_confirmation": "StrongPassword2!",
        },
    )
    post(second, "/login", data={"username": "bob", "password": "StrongPassword2!"})

    assert b"private note" not in second.get("/documents/notebook.md").data


def test_admin_can_view_account_summary(tmp_path):
    client = make_client(tmp_path, admin_password="University500!")
    post(client, "/logout")
    post(
        client,
        "/login",
        data={"username": "administrator", "password": "University500!"},
    )

    response = client.get("/admin")

    assert response.status_code == 200
    assert b"Account overview" in response.data


def test_admin_can_update_and_delete_user_accounts(tmp_path):
    client = make_client(tmp_path, admin_password="University500!")
    post(client, "/logout")
    post(
        client,
        "/login",
        data={"username": "administrator", "password": "University500!"},
    )

    response = post(client, "/admin/users/2/role", data={"role": "admin"})

    assert response.status_code == 302
    with closing(sqlite3.connect(client.application.config["DATABASE_PATH"])) as connection:
        assert connection.execute(
            "SELECT role FROM users WHERE id = 2"
        ).fetchone()[0] == "admin"

    response = post(client, "/admin/users/2/delete")

    assert response.status_code == 302
    with closing(sqlite3.connect(client.application.config["DATABASE_PATH"])) as connection:
        assert connection.execute(
            "SELECT id FROM users WHERE id = 2"
        ).fetchone() is None
    assert not (tmp_path / "notebooks" / "2").exists()


def test_admin_cannot_delete_self_or_last_admin(tmp_path):
    client = make_client(tmp_path, admin_password="University500!")
    post(client, "/logout")
    post(
        client,
        "/login",
        data={"username": "administrator", "password": "University500!"},
    )

    response = post(client, "/admin/users/1/delete")

    assert response.status_code == 302
    with closing(sqlite3.connect(client.application.config["DATABASE_PATH"])) as connection:
        assert connection.execute(
            "SELECT id FROM users WHERE id = 1"
        ).fetchone() is not None


def test_state_changes_require_csrf_token(tmp_path):
    client = make_client(tmp_path)
    client.get("/")

    response = client.post(
        "/",
        data={"document": "notebook.md", "note": "forged request"},
    )

    assert response.status_code == 400
    assert "forged request" not in notebook_path(tmp_path).read_text(
        encoding="utf-8"
    )
