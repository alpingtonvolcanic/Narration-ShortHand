document.addEventListener("DOMContentLoaded", () => {
  const note = document.querySelector("#note");
  const documentOptions = document.querySelectorAll('input[name="document"]');
  const narrationStatus = document.querySelector("#narration-status");
  const noteList = document.querySelector("#note-list");
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

  const loadDocument = async (filename) => {
    await loadNotes(filename);
  };

  const loadNotes = async (filename) => {
    noteList.textContent = "Loading notes...";
    try {
      const response = await fetch(
        `/documents/${encodeURIComponent(filename)}/notes`,
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      noteList.textContent = "";
      if (!data.notes.length) {
        noteList.textContent = "No timestamped notes yet.";
        return;
      }
      data.notes.forEach((item) => {
        const row = document.createElement("form");
        row.className = "note-item";
        const input = document.createElement("textarea");
        input.value = item.text;
        input.maxLength = 500;
        input.required = true;
        input.rows = 3;
        const label = document.createElement("span");
        label.textContent = item.timestamp;
        const save = document.createElement("button");
        save.type = "submit";
        save.textContent = "Save";
        const remove = document.createElement("button");
        remove.type = "button";
        remove.textContent = "Delete";
        const narrate = document.createElement("button");
        narrate.type = "button";
        narrate.textContent = "Narrate";
        row.append(label, input, save, remove, narrate);
        row.addEventListener("submit", async (event) => {
          event.preventDefault();
          await changeNote(filename, item.index, "POST", { text: input.value });
        });
        remove.addEventListener("click", async () => {
          try {
            await changeNote(filename, item.index, "DELETE");
          } catch (error) {
            narrationStatus.textContent = `Unable to delete note: ${error.message}`;
          }
        });
        narrate.addEventListener("click", async () => {
          narrate.disabled = true;
          narrationStatus.textContent = "Preparing note narration...";
          try {
            if (!("speechSynthesis" in window)) {
              throw new Error("Speech synthesis is not supported by this browser.");
            }
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(input.value);
            utterance.onend = () => {
              narrationStatus.textContent = "Finished narrating selected note.";
              narrate.disabled = false;
            };
            utterance.onerror = () => {
              narrationStatus.textContent = "Unable to narrate selected note.";
              narrate.disabled = false;
            };
            window.speechSynthesis.speak(utterance);
            narrationStatus.textContent = "Narrating selected note.";
          } catch (error) {
            narrationStatus.textContent = `Unable to narrate note: ${error.message}`;
            narrate.disabled = false;
          }
        });
        noteList.append(row);
      });
    } catch (error) {
      noteList.textContent = `Unable to load notes: ${error.message}`;
    }
  };

  const changeNote = async (filename, index, method, body) => {
    const response = await fetch(
      `/documents/${encodeURIComponent(filename)}/notes/${index}`,
      {
        method,
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: body ? JSON.stringify(body) : undefined,
      },
    );
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    await loadNotes(filename);
  };

  documentOptions.forEach((option) => {
    option.addEventListener("change", () => loadDocument(option.value));
  });

  const selected = document.querySelector('input[name="document"]:checked');
  if (selected) loadDocument(selected.value);

  note?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      note.form.requestSubmit();
    }
  });
});
