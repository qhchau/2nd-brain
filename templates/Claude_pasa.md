# File Structure — PASA AI

## Folder Rules

- `raw/` — immutable source files. Read / delete only. Never modify the content.
- `wiki-INDEX.md` — catalog of all wiki pages. Update on every ingest.
- `wiki-LOG.md` — append-only history. Append an entry before every operation.
- All wiki pages use a flat `wiki-<slug>.md` naming at root level. No subfolders.
- `CLAUDE.md` — this file. Co-evolved by <Full-Name> and Claude.

---
