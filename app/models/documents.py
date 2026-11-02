import re
from pathlib import Path


class DocumentStore:
    """Reads and appends timestamped notes to local UTF-8 documents."""

    def __init__(self, root, supported_extensions, excluded_names=()):
        self.root = Path(root).resolve()
        self.supported_extensions = {
            extension.lower() for extension in supported_extensions
        }
        self.excluded_names = {name.lower() for name in excluded_names}

    def list_documents(self):
        return sorted(
            (
                path
                for path in self.root.iterdir()
                if path.is_file()
                and path.suffix.lower() in self.supported_extensions
                and path.name.lower() not in self.excluded_names
            ),
            key=lambda path: path.name.lower(),
        )

    def ensure_default_document(self, filename):
        document = self.root / filename
        if document.exists():
            return
        document.write_text("", encoding="utf-8")

    def create_document(self, filename):
        if not filename or Path(filename).name != filename:
            raise ValueError("Choose a valid document name.")
        if filename.lower() in self.excluded_names:
            raise ValueError("That document name is reserved.")
        if Path(filename).suffix.lower() not in self.supported_extensions:
            raise ValueError("That file type is not supported.")
        document = (self.root / filename).resolve()
        if document.parent != self.root:
            raise ValueError("Documents must be in the local document directory.")
        if document.exists():
            raise ValueError("A document with that name already exists.")
        document.write_text("", encoding="utf-8")

    def delete_document(self, filename):
        if filename == "notebook.md":
            raise ValueError("The default notebook cannot be deleted.")
        document = self.get_document(filename)
        document.unlink()

    def get_document(self, filename):
        if not filename or Path(filename).name != filename:
            raise ValueError("Choose a valid document.")

        document = (self.root / filename).resolve()
        if document.parent != self.root:
            raise ValueError("Documents must be in the local document directory.")
        if document.suffix.lower() not in self.supported_extensions:
            raise ValueError("That file type is not supported.")
        if not document.is_file():
            raise FileNotFoundError("The selected document no longer exists.")
        return document

    def append_note(self, filename, note, timestamp):
        if "\n" in note or "\r" in note:
            raise ValueError("Notes must be a single line.")
        document = self.get_document(filename)
        content = document.read_text(encoding="utf-8")
        separator = "" if not content or content.endswith("\n") else "\n"
        stamped_note = f"{separator}- [{timestamp}] {note}\n"
        temporary = document.with_name(f".{document.name}.tmp")
        temporary.write_text(content + stamped_note, encoding="utf-8")
        temporary.replace(document)

    def list_notes(self, filename):
        content = self.get_document(filename).read_text(encoding="utf-8")
        notes = []
        pattern = re.compile(r"^- \[([^\]]+)\] (.*?)(?:\r?\n)?$")
        for line_number, line in enumerate(content.splitlines(keepends=True)):
            match = pattern.match(line)
            if match:
                notes.append(
                    {
                        "index": len(notes),
                        "timestamp": match.group(1),
                        "text": match.group(2),
                        "line_number": line_number,
                    }
                )
        return notes

    def update_note(self, filename, note_index, text):
        if "\n" in text or "\r" in text:
            raise ValueError("Notes must be a single line.")
        document = self.get_document(filename)
        lines = document.read_text(encoding="utf-8").splitlines(keepends=True)
        note_lines = [
            line_number
            for line_number, line in enumerate(lines)
            if re.match(r"^- \[[^\]]+\] .*?(?:\r?\n)?$", line)
        ]
        if note_index < 0 or note_index >= len(note_lines):
            raise ValueError("That note no longer exists.")
        line_number = note_lines[note_index]
        timestamp = re.match(r"^- \[([^\]]+)\]", lines[line_number]).group(1)
        ending = "\n" if lines[line_number].endswith("\n") else ""
        lines[line_number] = f"- [{timestamp}] {text}{ending}"
        self._write_content(document, "".join(lines))

    def delete_note(self, filename, note_index):
        document = self.get_document(filename)
        lines = document.read_text(encoding="utf-8").splitlines(keepends=True)
        note_lines = [
            line_number
            for line_number, line in enumerate(lines)
            if re.match(r"^- \[[^\]]+\] .*?(?:\r?\n)?$", line)
        ]
        if note_index < 0 or note_index >= len(note_lines):
            raise ValueError("That note no longer exists.")
        del lines[note_lines[note_index]]
        self._write_content(document, "".join(lines))

    @staticmethod
    def _write_content(document, content):
        temporary = document.with_name(f".{document.name}.tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(document)

    def read_document(self, filename):
        return self.get_document(filename).read_text(encoding="utf-8")
