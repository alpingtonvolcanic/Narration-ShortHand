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
        document = self.get_document(filename)
        content = document.read_text(encoding="utf-8")
        separator = "" if not content or content.endswith("\n") else "\n"
        stamped_note = f"{separator}- [{timestamp}] {note}\n"
        temporary = document.with_name(f".{document.name}.tmp")
        temporary.write_text(content + stamped_note, encoding="utf-8")
        temporary.replace(document)

    def read_document(self, filename):
        return self.get_document(filename).read_text(encoding="utf-8")
