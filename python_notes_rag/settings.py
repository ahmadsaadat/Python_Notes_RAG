# python_notes_rag/settings.py
import pathlib

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "qwen2.5:14b"

# 1. export notes
NOTES_DIR = pathlib.Path(__file__).parent / "notes"
NOTES_DIR.mkdir(exist_ok=True)

# 2. export chunks
CHUNKS_DIR = pathlib.Path(__file__).parent / "chunks"
CHUNKS_DIR.mkdir(exist_ok=True)

# 3. export embeddings
EMBEDDINGS_DIR = pathlib.Path(__file__).parent / "embeddings"
EMBEDDINGS_DIR.mkdir(exist_ok=True)

# 4. export db
DB_DIR = pathlib.Path(__file__).parent / "db"
DB_DIR.mkdir(exist_ok=True)