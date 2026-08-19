"""CLI for jot."""
import click
from pathlib import Path
from datetime import datetime

from jot.vault import Vault, Note, VAULT_DIR


@click.group()
@click.version_option()
def cli():
    """Self-hosted encrypted notes."""
    pass


@cli.command()
@click.option("--remote", default=None, help="Git remote URL for sync")
def init(remote):
    """Initialize note vault."""
    VAULT_DIR.mkdir(exist_ok=True)
    passphrase = click.prompt("Set vault passphrase", hide_input=True, confirmation_prompt=True)
    vault = Vault(passphrase)
    click.echo(f"✅ Vault initialized at {VAULT_DIR}")
    if remote:
        import subprocess
        subprocess.run(["git", "init"], cwd=VAULT_DIR, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", remote], cwd=VAULT_DIR, capture_output=True)
        click.echo(f"   Remote: {remote}")


@cli.command("new")
@click.argument("title", default="")
@click.option("--tag", "-t", multiple=True)
def new_note(title, tag):
    """Create a new note (opens $EDITOR)."""
    passphrase = click.prompt("Passphrase", hide_input=True)
    vault = Vault(passphrase)

    import tempfile, subprocess, os
    editor = os.environ.get("EDITOR", "nano")

    with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as f:
        if title:
            f.write(f"# {title}\n\n")
        tmp_path = f.name

    subprocess.run([editor, tmp_path])
    content = Path(tmp_path).read_text()
    Path(tmp_path).unlink()

    if not content.strip():
        click.echo("Empty note, discarded.")
        return

    now = datetime.now().isoformat()
    note = Note(
        id=datetime.now().strftime("%Y%m%d_%H%M%S"),
        title=title or content.split("\n")[0][:50],
        content=content,
        tags=list(tag),
        created=now,
        modified=now,
    )
    vault.save_note(note)
    click.echo(f"✅ Note saved: {note.title}")


@cli.command()
@click.argument("text")
@click.option("--tag", "-t", multiple=True)
def quick(text, tag):
    """Quick one-liner note."""
    passphrase = click.prompt("Passphrase", hide_input=True)
    vault = Vault(passphrase)
    now = datetime.now().isoformat()
    note = Note(
        id=datetime.now().strftime("%Y%m%d_%H%M%S"),
        title=text[:50],
        content=text,
        tags=list(tag),
        created=now,
        modified=now,
    )
    vault.save_note(note)
    click.echo(f"✅ Saved: {text[:60]}")


@cli.command("list")
def list_notes():
    """List recent notes."""
    vault = Vault()
    notes = vault.list_notes()
    if not notes:
        click.echo("No notes yet. Create one: jot new")
        return
    for n in sorted(notes, key=lambda x: x["created"], reverse=True)[:20]:
        tags = " ".join(f"[{t}]" for t in n.get("tags", []))
        click.echo(f"  {n['id']}  {n['title'][:50]} {tags}")


@cli.command()
@click.argument("query")
def search(query):
    """Search notes."""
    vault = Vault()
    results = vault.search(query)
    click.echo(f"Found {len(results)} notes:")
    for n in results:
        click.echo(f"  {n['id']}  {n['title']}")


@cli.command()
def sync():
    """Sync vault via git."""
    import subprocess
    subprocess.run(["git", "add", "."], cwd=VAULT_DIR)
    subprocess.run(["git", "commit", "-m", f"sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"], cwd=VAULT_DIR)
    subprocess.run(["git", "push"], cwd=VAULT_DIR)
    click.echo("✅ Synced")


if __name__ == "__main__":
    cli()
