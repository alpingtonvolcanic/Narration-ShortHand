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

Open <http://127.0.0.1:5000>. By default, the app lists supported documents
from the directory where it is started. Set `DOCUMENT_ROOT` to use another
local directory:

```bash
DOCUMENT_ROOT=/path/to/docs python app.py
```

If no default document exists, the app creates `narratornotes1.doc` and
selects it automatically. `README.md` and `requirements.txt` are intentionally
not shown as writable documents. Press Enter in the note field to submit; use
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

GitHub Actions runs the same test suite for pushes and pull requests in
`.github/workflows/ci.yml`.
