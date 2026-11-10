# Narrator-Shorthand

A small Flask MVC app for adding timestamped shorthand notes to local,
UTF-8-compatible document files.

## Programming Concepts

The application follows an MVC-style architecture with three related
components:

- Model – `UserDatabase` manages users, password hashes, roles, and
  notebook metadata in SQLite. `DocumentStore` manages each user's local
  UTF-8 document files and timestamped notes.
- View – Jinja2 templates in `templates/`, together with the CSS and
  JavaScript files in `static/`, provide the user interface.
- Controller – Flask blueprints in `app/controllers/` handle requests,
  authentication, authorization, document operations, and note operations.

Users authenticate with a signed Flask session. Passwords are hashed with
Werkzeug, usernames are stored as keyed hashes, and state-changing requests
are protected with CSRF tokens. Each account has its own notebook directory,
so authenticated users cannot access another user's notes through the
application.

## Technologies Used

- Programming language: Python 3
- Web framework: Flask 3
- Database: SQLite
- Database access: Python `sqlite3` with parameterized queries
- Authentication and password security: Flask sessions and Werkzeug
  password hashing
- Frontend: HTML, CSS, JavaScript, and Jinja2 templates
- Text-to-speech: Browser Web Speech API
- Development environment: Visual Studio Code and GitHub Codespaces
- Testing: pytest

The application does not use Flask-Login or Heroku Postgres. Administrator
credentials are configured through the `ADMIN_USERNAME` and `ADMIN_PASSWORD`
environment variables rather than hardcoded in the source code.

## Routing

The application registers two Flask blueprints: `auth` for account and
administrator features, and `notes` for notebook and document features.

| Method | Route | Description | Access |
| --- | --- | --- | --- |
| `GET`, `POST` | `/login` | Display the login form and authenticate a user. | Public |
| `GET`, `POST` | `/signup` | Display the signup form and create a user account. | Public |
| `POST` | `/logout` | Clear the current session. | Authenticated |
| `GET` | `/` | Display the current user's documents and add a note. | Authenticated |
| `POST` | `/documents` | Create a supported document in the user's notebook. | Authenticated |
| `GET` | `/documents/<filename>` | Return the selected document as JSON. | Authenticated |
| `GET` | `/documents/<filename>/notes` | Return parsed notes from a document as JSON. | Authenticated |
| `POST` | `/documents/<filename>/notes/<note_index>` | Update a note. | Authenticated |
| `DELETE` | `/documents/<filename>/notes/<note_index>` | Delete a note. | Authenticated |
| `POST` | `/documents/<filename>/delete` | Delete a user document. | Authenticated |
| `GET` | `/admin` | List accounts and display administrator controls. | Administrator |
| `POST` | `/admin/users/<user_id>/role` | Change an account's role. | Administrator |
| `POST` | `/admin/users/<user_id>/delete` | Delete an account and its notebook. | Administrator |

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> and create an account. Each account gets a
separate `notebook.md` under `DOCUMENT_ROOT/notebooks/`; notes cannot be read
by other users. The SQLite database stores keyed username hashes, password
hashes, account creation dates, roles, notebook paths, and last notebook update
timestamps. Set `DOCUMENT_ROOT` to use another local directory:

The application listens on `0.0.0.0:5000` by default so it works with
GitHub Codespaces port forwarding. Set `PORT` to use another port and open
that forwarded port in the Ports panel.

```bash
DOCUMENT_ROOT=/path/to/docs python app.py
```

Set a strong `SECRET_KEY` in production. To provision the administrator account,
set these environment variables before starting the application:

```bash
export SECRET_KEY='replace-with-a-long-random-value'
export ADMIN_USERNAME=administrator
export ADMIN_PASSWORD='set-this-outside-source-control'
export DEMO_PASSWORD='set-a-different-password-at-least-12-characters'
python app.py
```

These values must be set in the same terminal before starting the application.
They are not default passwords and are not stored in source control. With the
example usernames above, sign in at `/login` using:

```text
Administrator: administrator / the value of ADMIN_PASSWORD
Dummy account: demo1 or demo2 / the value of DEMO_PASSWORD
```

You do not create the demo users through the signup page. To create them,
export `DEMO_PASSWORD` and start the application; startup automatically creates
both `demo1` and `demo2` with that password. For example:

```bash
export DEMO_PASSWORD='DemoPassword123!'
python app.py
```

Then log in at `/login` as `demo1` or `demo2` with `DemoPassword123!`.

`ADMIN_PASSWORD` and `DEMO_PASSWORD` must each be 12-128 characters. The
administrator is created only when `ADMIN_PASSWORD` is set; the optional dummy
accounts are created only when `DEMO_PASSWORD` is set. If an account already
exists in `users.sqlite3`, changing an environment variable does not change
that account's password. Delete the local database only when resetting local
assignment data is acceptable, or use the application's account-management
process instead. Usernames must be 3-32 characters containing only letters,
numbers, `.`, `_`, or `-`. Press Enter in the note field to submit; use
Shift+Enter for a line break.

Notes are appended as `- [YYYY-MM-DD HH:MM UTC] note`. Supported extensions
are `.md`, `.txt`, `.rst`, `.adoc`, `.text`, `.log`, and `.doc`; these files
must contain UTF-8 text. The application does not parse binary Word `.doc` or
`.docx` files.

Use the Narrate button beside each note to use the browser's built-in Web
Speech API. This does not require `pyttsx3`, eSpeak, or a server-side speech
engine; the selected browser and operating system provide the voice.

## Test

```bash
pytest
```

GitHub Actions runs the test suite, linting, security scans, dependency audit,
and coverage checks for pushes and pull requests in
`.github/workflows/ci.yml`.
