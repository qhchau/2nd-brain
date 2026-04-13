<!-- upd:2026-04-13 -->
# File Structure — PASA AI

## Folder Rules

- `raw/` or `raw__` prefix in the root folder — immutable source files. Read / delete only. Never modify the content.
- `wiki-INDEX.md` — catalog of all wiki pages. Update on every ingest.
- `wiki-LOG.md` — append-only history. Append an entry before every operation.
- All wiki pages use a flat `wiki-<slug>.md` naming at root level. No subfolders.
- `CLAUDE.md` — this file. Co-evolved by <Full-Name> and Claude.

---

## First-Run Check

Before any ingest, check if `wiki-INDEX.md` and `wiki-LOG.md` exist in the root folder. If either is missing, create it now:
- `wiki-INDEX.md`: `# Wiki Index\n\n_No pages yet. Will be populated as you ingest files._`
- `wiki-LOG.md`: `# Operations Log\n\n_No operations yet. Updated automatically on each ingest, query, and lint._`

---
