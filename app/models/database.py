import hashlib
import hmac
import shutil
import sqlite3
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path

from werkzeug.security import (
    check_password_hash,
    generate_password_hash,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username_hash TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TEXT NOT NULL,
    notebook_path TEXT NOT NULL,
    last_notebook_update TEXT
)
"""


def _timestamp():
    return datetime.now(UTC).isoformat(timespec="seconds")


class UserDatabase:
    def __init__(self, path, username_key):
        self.path = Path(path)
        self.username_key = username_key.encode("utf-8")

    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def transaction(self):
        with closing(self.connect()) as connection, connection:
            yield connection

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.transaction() as connection:
            connection.execute(SCHEMA)

    def username_hash(self, username):
        normalized = username.strip().lower().encode("utf-8")
        return hmac.new(self.username_key, normalized, hashlib.sha256).hexdigest()

    def create_user(self, username, password, role="user"):
        try:
            with self.transaction() as connection:
                cursor = connection.execute(
                    "INSERT INTO users "
                    "(username_hash, password_hash, role, created_at, notebook_path) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        self.username_hash(username),
                        generate_password_hash(password),
                        role,
                        _timestamp(),
                        "",
                    ),
                )
                user_id = cursor.lastrowid
                notebook_path = f"notebooks/{user_id}/notebook.md"
                connection.execute(
                    "UPDATE users SET notebook_path = ? WHERE id = ?",
                    (notebook_path, user_id),
                )
                return user_id
        except sqlite3.IntegrityError as error:
            raise ValueError("That username is already registered.") from error

    def find_by_username(self, username):
        with closing(self.connect()) as connection:
            return connection.execute(
                "SELECT * FROM users WHERE username_hash = ?",
                (self.username_hash(username),),
            ).fetchone()

    def authenticate(self, username, password):
        user = self.find_by_username(username)
        if user and check_password_hash(user["password_hash"], password):
            return user
        return None

    def update_notebook(self, user_id):
        with self.transaction() as connection:
            connection.execute(
                "UPDATE users SET last_notebook_update = ? WHERE id = ?",
                (_timestamp(), user_id),
            )

    def list_users(self):
        with closing(self.connect()) as connection:
            return connection.execute(
                """
                SELECT id, role, created_at, last_notebook_update
                FROM users
                ORDER BY created_at
                """
            ).fetchall()

    def update_role(self, user_id, role):
        if role not in {"user", "admin"}:
            raise ValueError("Choose a valid account role.")
        with self.transaction() as connection:
            result = connection.execute(
                "UPDATE users SET role = ? WHERE id = ?",
                (role, user_id),
            )
            if result.rowcount == 0:
                raise ValueError("That account does not exist.")

    def delete_user(self, user_id, document_root):
        document_root = Path(document_root).resolve()
        notebook_root = (document_root / "notebooks").resolve()
        with self.transaction() as connection:
            user = connection.execute(
                "SELECT notebook_path FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if user is None:
                raise ValueError("That account does not exist.")
            connection.execute("DELETE FROM users WHERE id = ?", (user_id,))

        notebook_path = (document_root / user["notebook_path"]).resolve()
        if notebook_root not in notebook_path.parents:
            raise ValueError("The account notebook path is invalid.")
        if notebook_path.parent.exists():
            shutil.rmtree(notebook_path.parent)
