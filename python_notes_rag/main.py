import typer
import macnotesapp
from python_notes_rag import utils
from python_notes_rag import settings

app = typer.Typer()

@app.command()
def export():
    """1. Export Notes"""
    utils.request_permissions()

    app = macnotesapp.NotesApp()

    for note in app.notes():
        filename = note.name.replace("/", "-").replace(":", "-") + ".md"
        path = settings.OUTPUT_DIR / filename
        path.write_text(note.body, encoding="utf-8")

    print(f"Exported {len(app.notes())} notes to {settings.OUTPUT_DIR}")

@app.command()
def chunk():

    chunks = []

    for path in settings.OUTPUT_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        words = text.split()
        for i in range(0, len(words), settings.CHUNK_SIZE - settings.CHUNK_OVERLAP):
            chunk = "".join(words[i: i + settings.CHUNK_SIZE])
            if chunk.strip():
                chunks.append({
                    "source": path.name,
                    "chunk_index": i,
                    "text": chunk   
                })
    
    print(f"Created {len(chunks)} sequences from {len(list(settings.OUTPUT_DIR.iterdir()))} notes")
    return chunks
    

@app.command()
def query(question: str, top_k: int = 5):
    """Ask a question about your Notes"""
    ...

if __name__ == "__main__":
    app()