# File Structure — Claude Code CLI

## Folder Rules

- `raw/` — immutable source files. Read / delete only. Never modify the content.
- `wiki/` — you own this entirely. <Full-Name> reads it; you write and maintain it.
- `wiki/.system/index.md` — catalog of all wiki pages. Update on every ingest.
- `wiki/.system/log.md` — append-only history. Append an entry before every operation.
- `CLAUDE.md` — this file. Co-evolved by <Full-Name> and Claude.

### Subfolder rule
Create a subfolder inside `wiki/` only when 3+ pages share a clear category (e.g. `wiki/clients/` once Nissan, Toyota, GM each have their own page). When you move pages into a subfolder, update all cross-links and the index.

### Cross-link subfolder example
`[Nissan SubAmp Project](wiki/clients/nissan-subamp-project.md)`

---
