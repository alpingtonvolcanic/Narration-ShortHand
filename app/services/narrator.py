import pyttsx3


def narrate(text, output_path):
    """Render text to an audio file using the local pyttsx3 speech engine."""
    engine = pyttsx3.init()
    try:
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
    finally:
        engine.stop()
