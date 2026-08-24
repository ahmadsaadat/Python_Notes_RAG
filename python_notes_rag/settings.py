# python_notes_rag/settings.py
import pathlib

OUTPUT_DIR = pathlib.Path(__file__).parent / "notes"
OUTPUT_DIR.mkdir(exist_ok=True)
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50