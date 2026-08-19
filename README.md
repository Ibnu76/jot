# jot

Self-hosted note-taking with end-to-end encryption and git-based sync. Own your data — no cloud, no subscription, no tracking.

## Install

```bash
pip install jot-notes
```

## Quick Start

```bash
# Init vault (creates encrypted store)
jot init

# Write notes
jot new "project ideas"          # opens $EDITOR
jot quick "remember: deploy fri" # one-liner

# Search & browse
jot list
jot search "deploy"
jot view 3

# Sync (git-based)
jot sync
```

## Philosophy

- **Local-first** — notes live on your machine, encrypted at rest
- **Git sync** — push/pull to any git remote (GitHub private repo, self-hosted gitea)
- **E2E encrypted** — AES-256-GCM, key derived from passphrase (argon2id)
- **Plain markdown** — write in your editor, no proprietary format
- **Fast** — instant search via local index, no network needed

## Architecture

```
~/.jot/
├── vault/               # encrypted note files (.enc)
│   ├── 20240315_142300.enc
│   └── 20240316_091500.enc
├── index.db             # local search index (SQLite FTS5)
├── config.yaml          # preferences
└── .git/                # sync via git
```

Notes are encrypted individually — git sees binary blobs, never plaintext.
Decryption happens only in memory when you read/search.

## Commands

```bash
jot init                     # create vault + set passphrase
jot new [title]              # new note in $EDITOR
jot quick "text"             # one-liner note
jot list                     # recent notes
jot search "query"           # FTS5 full-text search
jot view <id>                # decrypt + display
jot edit <id>                # decrypt + edit + re-encrypt
jot rm <id>                  # delete note
jot tags                     # list all tags
jot tag <tag>                # notes with tag
jot export <id> [--to file]  # export decrypted markdown
jot sync                     # git add + commit + push
jot sync pull                # git pull + reindex
```

## Encryption

```
passphrase → argon2id(time=3, mem=256MB) → 256-bit key
note + random nonce → AES-256-GCM → .enc file
```

- Each note has its own random nonce
- Key never written to disk
- Passphrase cached in memory for session (configurable TTL)
- Optional: hardware key (YubiKey via FIDO2)

## Sync Setup

```bash
# Use any git remote
jot init --remote git@github.com:user/notes-vault.git

# Or add remote later
cd ~/.jot && git remote add origin <url>
jot sync  # auto push/pull
```

Works with: GitHub (private), Gitea, Forgejo, bare repos on any server.

## Config

```yaml
# ~/.jot/config.yaml
editor: nvim
passphrase_ttl: 3600        # cache passphrase 1h (0 = ask every time)
auto_sync: true             # sync on every write
default_tags: []

encryption:
  algorithm: aes-256-gcm
  kdf: argon2id
  kdf_time: 3
  kdf_memory: 262144        # 256MB

sync:
  remote: origin
  auto_push: true
  auto_pull: true
```

## Why Not X?

| Tool | Issue |
|------|-------|
| Notion/Obsidian Sync | Cloud dependency, no E2E encryption |
| Apple Notes | Vendor lock-in, weak search |
| Standard Notes | Subscription for sync |
| Plain markdown + git | No encryption at rest |
| **jot** | Encrypted + git sync + local-first + free |

## License

MIT
