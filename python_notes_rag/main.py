import json
import sys
import typer
import macnotesapp
import ollama
import lancedb
import shutil
import pandas
from typer.main import get_command
from python_notes_rag import utils
from python_notes_rag import settings

app = typer.Typer()

@app.command()
def notes():
    """1. Export Notes"""

    for file in settings.NOTES_DIR.glob("*"):
        file.unlink()

    app = macnotesapp.NotesApp()

    for note in app.notes():
        filename = note.name.replace("/", "-").replace(":", "-") + ".md"
        path = settings.NOTES_DIR / filename
        path.write_text(note.body, encoding="utf-8")

    print(f"Exported {len(app.notes())} notes to {settings.NOTES_DIR}")

@app.command()
def chunk():
    """2. Chunk Notes"""

    for file in settings.CHUNKS_DIR.glob("*"):
        file.unlink()

    for path in settings.NOTES_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        words = text.split()
        for i in range(0, len(words), settings.CHUNK_SIZE - settings.CHUNK_OVERLAP):
            chunk = " ".join(words[i: i + settings.CHUNK_SIZE])
            if chunk.strip():
                chunk = ({
                    "source": path.name,
                    "chunk_index": i,
                    "text": chunk   
                })
                chunk_file = settings.CHUNKS_DIR / f"{path.stem}_{i}.json"
                chunk_file.write_text(json.dumps(chunk), encoding="utf-8")

    print(f"Exported {len(list(settings.CHUNKS_DIR.glob('*.json')))} chunks to {settings.CHUNKS_DIR}")

@app.command()  
def embed():
    """3. Embedding Notes"""

    for file in settings.EMBEDDINGS_DIR.glob("*"):
        file.unlink()

    with utils.ollama_server():
        for path in settings.CHUNKS_DIR.iterdir():
            chunk_data = json.loads(path.read_text(encoding="utf-8"))
            chunk_data["vector"] = ollama.embed(model=settings.EMBED_MODEL, input=chunk_data["text"])["embeddings"][0]
            out_path = settings.EMBEDDINGS_DIR / path.name
            out_path.write_text(json.dumps(chunk_data), encoding="utf-8")

    print(f"Exported embeddings {len(list(settings.EMBEDDINGS_DIR.iterdir()))} to {settings.EMBEDDINGS_DIR}")
    ...


@app.command()  
def db():
    """4. Store embeddings in LanceDB"""

    shutil.rmtree(settings.DB_DIR)
    settings.DB_DIR.mkdir()

    records = []
    for path in settings.EMBEDDINGS_DIR.iterdir():
        data = json.loads(path.read_text(encoding="utf-8"))
        records.append(data)

    db = lancedb.connect(str(settings.DB_DIR))
    db.create_table("notes", data=records, mode="overwrite")

    print(f"Stored {len(records)} embeddings in LanceDB at {settings.DB_DIR}")

@app.command()
def query(question: str, top_k: int = 5):
    """5. Query your Notes"""
    db = lancedb.connect(str(settings.DB_DIR))
    table = db.open_table("notes")

    with utils.ollama_server():
        question_vector = ollama.embed(model=settings.EMBED_MODEL, input=question)["embeddings"][0]
        results = table.search(question_vector).limit(top_k).to_list()
        context = "\n\n---\n\n".join(r["text"] for r in results)

        for chunk in ollama.chat(
            model=settings.CHAT_MODEL,
            messages=[{
                "role": "user",
                "content": f"Answer based only on these notes:\n\n{context}\n\nQuestion: {question}"
            }],
            stream=True
        ):
            print(chunk["message"]["content"], end="", flush=True)

@app.command()
def inspect(n: int = 10):
    """inspect db"""
    db = lancedb.connect(str(settings.DB_DIR))
    table = db.open_table("notes")
    pandas.set_option("display.colheader_justify", "left")
    print(table.to_pandas().head(n))


def is_trained() -> bool:
    try:
        db = lancedb.connect(str(settings.DB_DIR))
        return db.open_table("notes").count_rows() > 0
    except Exception:
        return False


def train():
    """Run the full RAG pipeline: export notes, chunk, embed, and store them."""
    print("Training on your notes (export -> chunk -> embed -> store)...")
    cli = get_command(app)
    for step in ("notes", "chunk", "embed", "db"):
        cli.main(args=[step], standalone_mode=False)
    print("Training complete.\n")


def ask(question: str, top_k: int = 5):
    """Answer a question using the existing RAG index. Assumes an Ollama server is already running."""
    db = lancedb.connect(str(settings.DB_DIR))
    table = db.open_table("notes")

    question_vector = ollama.embed(model=settings.EMBED_MODEL, input=question)["embeddings"][0]
    results = table.search(question_vector).limit(top_k).to_list()
    context = "\n\n---\n\n".join(r["text"] for r in results)

    for chunk in ollama.chat(
        model=settings.CHAT_MODEL,
        messages=[{
            "role": "user",
            "content": f"Answer based only on these notes:\n\n{context}\n\nQuestion: {question}"
        }],
        stream=True
    ):
        print(chunk["message"]["content"], end="", flush=True)
    print()


SLASH_COMMANDS = {
    "/retrain": "Re-run the RAG pipeline (export, chunk, embed, store) from scratch.",
    "/help": "Show this help.",
    "/exit": "Leave the chat.",
}


def chat():
    """Chatbot REPL: ask questions about your notes. /retrain, /help, /exit are recognized as commands."""

    if not is_trained():
        train()

    print("Ask a question about your notes. Commands: /retrain, /help, /exit\n")

    with utils.ollama_server():
        while True:
            try:
                line = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not line:
                continue

            if line in ("/exit", "/quit"):
                break

            if line == "/help":
                for command, description in SLASH_COMMANDS.items():
                    print(f"  {command:<10} {description}")
                continue

            try:
                if line == "/retrain":
                    train()
                    continue

                print("bot> ", end="", flush=True)
                ask(line)
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    utils.system_check()
    if len(sys.argv) > 1:
        app()
    else:
        chat()