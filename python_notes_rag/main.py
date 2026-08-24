import typer
import macnotesapp
import pathlib
from python_notes_rag import utils

app = typer.Typer()

@app.command()
def sync():
    """Export Apple Notes"""
    OUTPUT_DIR = pathlib.Path(__file__).parent.parent / "python_notes_rag" / "notes"
    OUTPUT_DIR.mkdir(exist_ok=True)
    utils.request_permissions()

    app = macnotesapp.NotesApp()

    for note in app.notes():
        filename = note.name.replace("/", "-").replace(":", "-") + ".md"
        path = OUTPUT_DIR / filename
        path.write_text(note.body, encoding="utf-8")

    print(f"Exported {len(app.notes())} notes to {OUTPUT_DIR}")

@app.command()
def query(question: str, top_k: int = 5):
    """Ask a question about your Notes"""
    ...

if __name__ == "__main__":
    app()