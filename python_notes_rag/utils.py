import subprocess
from contextlib import contextmanager
import time

from python_notes_rag import settings

REQUIRED_MODELS = [settings.EMBED_MODEL, settings.CHAT_MODEL]

def system_check():

    ollama_check = subprocess.run(["which", "ollama"], capture_output=True)

    if ollama_check.returncode != 0:
        raise SystemExit("Ollama not found. Install it with: brew install ollama")

    notes_permission = subprocess.run(
        ["osascript", "-e", 'tell application "Notes" to get name of every note'],
        capture_output=True,
        text=True
    )
    if notes_permission.returncode != 0:
        print("Permission denied. Please allow access to Notes in System Settings → Privacy & Security → Automation")
        raise SystemExit(1)

    with ollama_server():
        models_list = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if models_list.returncode != 0:
            raise SystemExit("Could not list Ollama models. Is Ollama installed correctly?")

        installed_models = models_list.stdout
        missing_models = [model for model in REQUIRED_MODELS if model not in installed_models]

        if missing_models:
            pull_commands = "\n".join(f"  ollama pull {model}" for model in missing_models)
            raise SystemExit(
                f"Missing required Ollama model(s): {', '.join(missing_models)}\n"
                f"Install with:\n{pull_commands}"
            )

@contextmanager
def ollama_server():
    process = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    try:
        yield process
    finally:
        process.terminate()
        process.wait()