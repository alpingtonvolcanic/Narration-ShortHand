from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import (
    Blueprint,
    after_this_request,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from app.models.documents import DocumentStore
from app.services.narrator import narrate

notes = Blueprint("notes", __name__)


def _store():
    return DocumentStore(
        current_app.config["DOCUMENT_ROOT"],
        current_app.config["SUPPORTED_DOCUMENT_EXTENSIONS"],
        current_app.config["EXCLUDED_DOCUMENT_NAMES"],
    )


@notes.route("/", methods=["GET", "POST"])
def index():
    store = _store()
    documents = store.list_documents()
    selected_document = (
        request.form.get("document", current_app.config["DEFAULT_DOCUMENT"])
        if request.method == "POST"
        else current_app.config["DEFAULT_DOCUMENT"]
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


@notes.get("/documents/<path:filename>")
def document_contents(filename):
    try:
        content = _store().read_document(filename)
    except (OSError, UnicodeError, ValueError, FileNotFoundError) as error:
        return jsonify(error=str(error)), 404
    return jsonify(filename=filename, content=content)


@notes.post("/documents/<path:filename>/narrate")
def narrate_document(filename):
    try:
        content = _store().read_document(filename)
        if not content.strip():
            return jsonify(error="The selected document is empty."), 400
        with NamedTemporaryFile(suffix=".wav", delete=False) as temporary:
            output_path = Path(temporary.name)
        narrate(content, output_path)
    except (OSError, UnicodeError, ValueError, FileNotFoundError, RuntimeError) as error:
        if "output_path" in locals():
            output_path.unlink(missing_ok=True)
        return jsonify(error=str(error)), 500

    @after_this_request
    def remove_audio(response):
        output_path.unlink(missing_ok=True)
        return response

    return send_file(output_path, mimetype="audio/wav", download_name="narration.wav")
