"""Encrypted vault management."""
from __future__ import annotations
import json
import os
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

VAULT_DIR = Path.home() / ".jot"
NOTES_DIR = VAULT_DIR / "vault"
INDEX_FILE = VAULT_DIR / "index.json"


@dataclass
class Note:
    id: str
    title: str
    content: str
    tags: list[str] = field(default_factory=list)
    created: str = ""
    modified: str = ""


class Vault:
    """Encrypted note storage."""

    def __init__(self, passphrase: str | None = None):
        self._key: bytes | None = None
        if passphrase:
            self._derive_key(passphrase)
        VAULT_DIR.mkdir(exist_ok=True)
        NOTES_DIR.mkdir(exist_ok=True)

    def _derive_key(self, passphrase: str) -> None:
        """Derive encryption key from passphrase using scrypt."""
        salt = self._get_or_create_salt()
        if HAS_CRYPTO:
            kdf = Scrypt(salt=salt, length=32, n=2**16, r=8, p=1)
            self._key = kdf.derive(passphrase.encode())
        else:
            # Fallback: hashlib (less secure but works without cryptography)
            self._key = hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, 100_000)

    def _get_or_create_salt(self) -> bytes:
        salt_file = VAULT_DIR / ".salt"
        if salt_file.exists():
            return salt_file.read_bytes()
        salt = os.urandom(32)
        salt_file.write_bytes(salt)
        return salt

    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt text with AES-256-GCM."""
        if not self._key:
            raise RuntimeError("Vault locked — provide passphrase")
        nonce = os.urandom(12)
        if HAS_CRYPTO:
            aesgcm = AESGCM(self._key)
            ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
        else:
            # Simplified XOR for demo (NOT production-safe)
            ct = bytes(a ^ b for a, b in zip(plaintext.encode(), (self._key * 100)[:len(plaintext)]))
        return nonce + ct

    def decrypt(self, ciphertext: bytes) -> str:
        """Decrypt AES-256-GCM ciphertext."""
        if not self._key:
            raise RuntimeError("Vault locked — provide passphrase")
        nonce = ciphertext[:12]
        ct = ciphertext[12:]
        if HAS_CRYPTO:
            aesgcm = AESGCM(self._key)
            return aesgcm.decrypt(nonce, ct, None).decode()
        else:
            return bytes(a ^ b for a, b in zip(ct, (self._key * 100)[:len(ct)])).decode()

    def save_note(self, note: Note) -> None:
        """Encrypt and save a note."""
        data = json.dumps({
            "title": note.title,
            "content": note.content,
            "tags": note.tags,
            "created": note.created,
            "modified": note.modified,
        })
        encrypted = self.encrypt(data)
        note_path = NOTES_DIR / f"{note.id}.enc"
        note_path.write_bytes(encrypted)
        self._update_index(note)

    def load_note(self, note_id: str) -> Note:
        """Decrypt and load a note."""
        note_path = NOTES_DIR / f"{note_id}.enc"
        if not note_path.exists():
            raise FileNotFoundError(f"Note {note_id} not found")
        encrypted = note_path.read_bytes()
        data = json.loads(self.decrypt(encrypted))
        return Note(id=note_id, **data)

    def list_notes(self) -> list[dict]:
        """List notes from index (no decryption needed)."""
        if INDEX_FILE.exists():
            return json.loads(INDEX_FILE.read_text())
        return []

    def search(self, query: str) -> list[dict]:
        """Search notes by title/tags in index."""
        index = self.list_notes()
        q = query.lower()
        return [n for n in index if q in n.get("title", "").lower() or q in str(n.get("tags", []))]

    def _update_index(self, note: Note) -> None:
        """Update search index (unencrypted metadata only)."""
        index = self.list_notes()
        # Remove existing entry
        index = [n for n in index if n["id"] != note.id]
        index.append({
            "id": note.id,
            "title": note.title,
            "tags": note.tags,
            "created": note.created,
            "modified": note.modified,
        })
        INDEX_FILE.write_text(json.dumps(index, indent=2))
