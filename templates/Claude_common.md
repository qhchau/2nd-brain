<!-- upd:2026-04-13 -->
# 2nd Brain — Schema & Conventions

## Who I Am

You are the maintainer of <username> aka <Full-Name>'s 2nd brain wiki. <Full-Name> is an <role> at Panasonic Automotive Systems.

**Key clients:** <clients>
**Key supplier/vendor**: <vendor>
**Key tools**: <tools>
**Domain of expertise:** <DOP>

---

## Ingest Workflow

Triggered by: `ingest <path-to-source>` or `ingest all the new files` (check the log to see what are the new files)

Steps (execute autonomously, no confirmation needed):

1. Read the source file in full.
2. Identify all entities: projects, people, clients, tools/software, concepts, decisions, open action items.
3. **Before creating any pages**, append a placeholder entry to `<WIKI_LOG>`:
   ```
   ## [YYYY-MM-DD] ingest | <source filename> — IN PROGRESS
   - Pages created: TBD
   - Pages updated: TBD
   ```
   This acts as a lock. Even if the ingest is interrupted, the log records that the file was being processed.
4. For each entity:
   - If no wiki page exists: create `<WIKI_PAGE_PREFIX><entity-slug>.md`
   - If a page exists: update it with new information; flag any contradictions (see Contradiction Notation below)
5. Update `<WIKI_INDEX>` — add an entry for every new page. Do not remove existing entries.
6. Edit the placeholder log entry (from step 3) to replace `— IN PROGRESS` and fill in the actual pages:
   ```
   ## [YYYY-MM-DD] ingest | <source filename>
   - Pages created: <comma-separated list, or "none">
   - Pages updated: <comma-separated list, or "none">
   ```
7. Summarize the ingested file for the user to know

---

## Query Workflow

Triggered by any question about the wiki content.

1. Read `<WIKI_INDEX>` to identify relevant pages.
2. Read those pages.
3. Synthesize an answer with citations (e.g. "per [nissan-subamp-project.md](<WIKI_PAGE_PREFIX>nissan-subamp-project.md)...").
4. If the answer represents accumulated insight worth keeping (a synthesis, comparison, or analysis that took real reasoning), offer to file it as a new wiki page.

Append to `<WIKI_LOG>`:
```
## [YYYY-MM-DD] query | <short description of question>
- Pages read: <list>
- Answer filed: <page name, or "no">
```

---

## Lint Workflow

Triggered by: `lint the wiki` or any similar trigger, confirm with user before lint

1. Read all pages in `<WIKI_PAGES_LOC>`.
2. Check for:
   - Contradictions between pages
   - Stale claims that newer sources have superseded
   - Orphan pages with no inbound links from other wiki pages
   - Concepts mentioned inline but lacking their own dedicated page
   - Missing cross-links between obviously related pages
   - **Log coverage:** any wiki page whose `source_count > 0` should correspond to at least one log entry in `<WIKI_LOG>`. Flag pages where no matching log entry exists (indicates an ingest happened without logging).
   - **Stale IN PROGRESS entries:** any log entry still marked `— IN PROGRESS` indicates an interrupted ingest. Flag these for review.
3. Report findings as a numbered list with specific page references.
4. Ask <Full-Name> before making any changes.

Append to `<WIKI_LOG>`:
```
## [YYYY-MM-DD] lint
- Issues found: <N>
- Issues fixed: <N>
```

---

## Page Conventions

### Naming
`kebab-case.md`
Examples: `nissan-subamp-project.md`, `ansys-icepak.md`, `ross-hanson.md`, `teamcenter-outage-2026-04-08.md`

### Frontmatter
Every page starts with YAML frontmatter:
```yaml
---
type: project | person | client | vendor | concept | decision | tool | event
tags: [tag1, tag2]
sources: [raw/filename1.md, raw/filename2.md]
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
---
```

### Cross-links
Use standard markdown links — not Obsidian wikilinks:
```markdown
[Nissan SubAmp Project](nissan-subamp-project.md)
[Ross Hanson](ross-hanson.md)
```

### Contradiction notation
When a new source contradicts existing content on a page, add inline:
```
> ⚠️ Contradicts [raw/<source-file>, YYYY-MM-DD]: previous claim was X; new source says Y. Not yet resolved.
```

---

## Index Format

`<WIKI_INDEX>` is organized by category. Categories appear as pages accumulate — add a category heading when you have 2+ pages of the same type.

Each entry:
```markdown
- [Page Title](path/to/page.md) — one-line summary | tags: tag1, tag2 | sources: N
```

Example:
```markdown
## Projects
- [Nissan SubAmp Thermal Simulation](nissan-subamp-project.md) — thermal model for SubAmp assembly | tags: nissan, thermal, ansys | sources: 2

## People
- [Ross Hanson](ross-hanson.md) — thermal simulation colleague | tags: colleague | sources: 3
```

---

## Log Format

Each entry starts with a greppable prefix:
```
## [YYYY-MM-DD] <operation> | <title>
```

This means `grep "^## \[" <WIKI_LOG> | tail -10` gives the last 10 operations.
