# Narrator-Shorthand

A small Flask MVC app for adding timestamped shorthand notes to local,
UTF-8-compatible document files.

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

Use **Narrate open document** below the preview to generate local speech with
`pyttsx3`. On Linux, install the system speech engine if needed:

```bash
sudo apt-get install espeak
```

## Test

```bash
pytest
```

GitHub Actions runs the test suite, linting, security scans, dependency audit,
and coverage checks for pushes and pull requests in
`.github/workflows/ci.yml`.
