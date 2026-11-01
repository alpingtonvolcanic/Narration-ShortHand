from app import create_app
from app.controllers import notes as notes_controller


def test_default_document_is_created_and_excluded_files_are_hidden(tmp_path):
    (tmp_path / "README.md").write_text("project docs\n", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("Flask\n", encoding="utf-8")
    client = create_app(
        {"TESTING": True, "SECRET_KEY": "test-key", "DOCUMENT_ROOT": tmp_path}
    ).test_client()

    response = client.get("/")

    assert (tmp_path / "narratornotes1.doc").exists()
    assert b"narratornotes1.doc" in response.data
    assert b"README.md" not in response.data
    assert b"requirements.txt" not in response.data


def test_note_is_appended_with_utc_timestamp(tmp_path):
    document = tmp_path / "handoff.md"
    document.write_text("# Handoff\n", encoding="utf-8")
    client = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "DOCUMENT_ROOT": tmp_path,
        }
    ).test_client()

    response = client.post(
        "/",
        data={"document": "handoff.md", "note": "CI is ready for review"},
    )

    assert response.status_code == 302
    assert "- [" in document.read_text(encoding="utf-8")
    assert "CI is ready for review" in document.read_text(encoding="utf-8")


def test_document_contents_are_displayed(tmp_path):
    document = tmp_path / "handoff.md"
    document.write_text("Current sprint status", encoding="utf-8")
    client = create_app(
        {"TESTING": True, "SECRET_KEY": "test-key", "DOCUMENT_ROOT": tmp_path}
    ).test_client()

    response = client.get("/documents/handoff.md")

    assert response.status_code == 200
    assert response.json == {
        "filename": "handoff.md",
        "content": "Current sprint status",
    }


def test_document_can_be_narrated(tmp_path, monkeypatch):
    document = tmp_path / "handoff.md"
    document.write_text("Narrate this status", encoding="utf-8")

    def fake_narrate(text, output_path):
        assert text == "Narrate this status"
        output_path.write_bytes(b"fake audio")

    monkeypatch.setattr(notes_controller, "narrate", fake_narrate)
    client = create_app(
        {"TESTING": True, "SECRET_KEY": "test-key", "DOCUMENT_ROOT": tmp_path}
    ).test_client()

    response = client.post("/documents/handoff.md/narrate")

    assert response.status_code == 200
    assert response.mimetype == "audio/wav"
    assert response.data == b"fake audio"


def test_invalid_document_path_is_rejected(tmp_path):
    document = tmp_path / "handoff.md"
    document.write_text("unchanged\n", encoding="utf-8")
    client = create_app(
        {"TESTING": True, "SECRET_KEY": "test-key", "DOCUMENT_ROOT": tmp_path}
    ).test_client()

    response = client.post("/", data={"document": "../handoff.md", "note": "bad"})

    assert response.status_code == 200
    assert document.read_text(encoding="utf-8") == "unchanged\n"
