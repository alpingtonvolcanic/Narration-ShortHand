document.addEventListener("DOMContentLoaded", () => {
  const note = document.querySelector("#note");
  const documentContent = document.querySelector("#document-content");
  const previewName = document.querySelector("#preview-name");
  const documentOptions = document.querySelectorAll('input[name="document"]');
  const narrateButton = document.querySelector("#narrate-document");
  const narrationStatus = document.querySelector("#narration-status");
  let openFilename = "";

  const loadDocument = async (filename) => {
    openFilename = filename;
    narrateButton.disabled = true;
    previewName.textContent = filename;
    documentContent.textContent = "Loading document...";
    try {
      const response = await fetch(`/documents/${encodeURIComponent(filename)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      documentContent.textContent = data.content || "(Document is empty)";
      narrateButton.disabled = !data.content;
    } catch (error) {
      documentContent.textContent = `Unable to load document: ${error.message}`;
    }
  };

  documentOptions.forEach((option) => {
    option.addEventListener("change", () => loadDocument(option.value));
  });

  const selected = document.querySelector('input[name="document"]:checked');
  if (selected) loadDocument(selected.value);

  narrateButton?.addEventListener("click", async () => {
    narrateButton.disabled = true;
    narrationStatus.textContent = "Preparing narration...";
    try {
      const response = await fetch(
        `/documents/${encodeURIComponent(openFilename)}/narrate`,
        { method: "POST" },
      );
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error);
      }
      const audio = new Audio(URL.createObjectURL(await response.blob()));
      audio.onended = () => URL.revokeObjectURL(audio.src);
      await audio.play();
      narrationStatus.textContent = "Narrating open document.";
    } catch (error) {
      narrationStatus.textContent = `Unable to narrate document: ${error.message}`;
    } finally {
      narrateButton.disabled = false;
    }
  });

  note?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      note.form.requestSubmit();
    }
  });
});
