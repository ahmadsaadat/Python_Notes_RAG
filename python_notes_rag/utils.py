import subprocess
from contextlib import contextmanager
import time

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
    
@contextmanager
def ollama_server():
    process = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    try:
        yield process
    finally:
        process.terminate()
        process.wait()