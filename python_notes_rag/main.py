import json
import typer
import macnotesapp
import ollama
import lancedb
import shutil
import pandas
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
            chunk_data["vector"] = ollama.embed(model="nomic-embed-text", input=chunk_data["text"])["embeddings"][0]
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
        question_vector = ollama.embed(model="nomic-embed-text", input=question)["embeddings"][0]
        results = table.search(question_vector).limit(top_k).to_list()
        context = "\n\n---\n\n".join(r["text"] for r in results)

        for chunk in ollama.chat(
            model="qwen2.5:14b",
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


if __name__ == "__main__":
    utils.system_check()
    app()