from datetime import UTC, datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.controllers.auth import database, login_required
from app.models.documents import DocumentStore

notes = Blueprint("notes", __name__)


def _store():
    notebook_root = current_app.config["DOCUMENT_ROOT"] / "notebooks" / str(g.user["id"])
    notebook_root.mkdir(parents=True, exist_ok=True)
    return DocumentStore(
        notebook_root,
        current_app.config["SUPPORTED_DOCUMENT_EXTENSIONS"],
        current_app.config["EXCLUDED_DOCUMENT_NAMES"],
    )


@notes.route("/", methods=["GET", "POST"])
@login_required
def index():
    _store().ensure_default_document("notebook.md")
    store = _store()
    documents = store.list_documents()
    selected_document = (
        request.form.get("document", "notebook.md")
        if request.method == "POST"
        else "notebook.md"
    )

    if request.method == "POST":
        note = request.form.get("note", "").strip()
        if not selected_document:
            flash("Select a document before submitting a note.", "error")
        elif not note:
            flash("Enter a short note before submitting.", "error")
        elif len(note) > 500:
            flash("Notes must be 500 characters or fewer.", "error")
        else:
            try:
                timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
                store.append_note(selected_document, note, timestamp)
                database().update_notebook(session["user_id"])
            except (OSError, UnicodeError, ValueError, FileNotFoundError) as error:
                flash(str(error), "error")
            else:
                flash(f"Note added to {selected_document}.", "success")
                return redirect(url_for("notes.index"))

    return render_template(
        "notes/index.html",
        documents=documents,
        selected_document=selected_document,
    )


@notes.post("/documents")
@login_required
def create_document():
    filename = request.form.get("filename", "").strip()
    try:
        _store().create_document(filename)
    except (OSError, ValueError) as error:
        flash(str(error), "error")
    else:
        flash(f"Created {filename}.", "success")
    return redirect(url_for("notes.index"))


@notes.post("/documents/<path:filename>/delete")
@login_required
def delete_document(filename):
    try:
        _store().delete_document(filename)
    except (OSError, ValueError, FileNotFoundError) as error:
        flash(str(error), "error")
    else:
        flash(f"Deleted {filename}.", "success")
    return redirect(url_for("notes.index"))


@notes.get("/documents/<path:filename>")
@login_required
def document_contents(filename):
    try:
        content = _store().read_document(filename)
    except (OSError, UnicodeError, ValueError, FileNotFoundError) as error:
        return jsonify(error=str(error)), 404
    return jsonify(filename=filename, content=content)


@notes.get("/documents/<path:filename>/notes")
@login_required
def document_notes(filename):
    try:
        return jsonify(notes=_store().list_notes(filename))
    except (OSError, UnicodeError, ValueError, FileNotFoundError) as error:
        return jsonify(error=str(error)), 404


@notes.post("/documents/<path:filename>/notes/<int:note_index>")
@login_required
def update_note(filename, note_index):
    text = request.get_json(silent=True) or {}
    try:
        note_text = text["text"].strip()
        if not note_text or len(note_text) > 500:
            raise ValueError("Notes must be between 1 and 500 characters.")
        _store().update_note(filename, note_index, note_text)
        database().update_notebook(session["user_id"])
    except (KeyError, OSError, UnicodeError, ValueError, FileNotFoundError) as error:
        return jsonify(error=str(error)), 400
    return jsonify(success=True)


@notes.delete("/documents/<path:filename>/notes/<int:note_index>")
@login_required
def delete_note(filename, note_index):
    try:
        _store().delete_note(filename, note_index)
        database().update_notebook(session["user_id"])
    except (OSError, UnicodeError, ValueError, FileNotFoundError) as error:
        return jsonify(error=str(error)), 400
    return jsonify(success=True)

@notes.route("/information")
@login_required
def information():
    return render_template("notes/information.html")
