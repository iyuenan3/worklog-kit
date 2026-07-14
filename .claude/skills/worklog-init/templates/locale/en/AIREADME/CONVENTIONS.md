# CONVENTIONS

## Diary (minimal contract)
- File: `diaries/YYYY-MM-DD.md`; title per config `diary_title_template`
- Attribution: 00:00 until `day_boundary` belongs to the previous day; timezone per config `timezone`
- Structure is soft: beyond the filename and append-only rule, sections may evolve freely (record evolution in DECISIONS)

## Wiki project-page frontmatter (contract, refreshed nightly by ingest)

    ---
    last_updated: YYYY-MM-DD
    source_count: N          # number of diaries mentioning this project (compounding metric)
    diaries: ["[[YYYY-MM-DD]]", ...]
    path: /abs/path          # optional: slug disambiguation anchor (written by ingest when same-named projects coexist; stable identity across nights)
    ---

## Project recording levels (config projects)
detail (full record + project page) / summary (one line) / presence (existence + count only) / exclude (absent); an empty `.worklogignore` in a project root or any ancestor directory = permanent exclude (vetoes the whole subtree; nested repos, submodules, and worktrees included).

## Writing
- Language per config `language`; zh enables the Chinese punctuation consistency gate

## Todo system (Obsidian Tasks syntax; degrades gracefully to plain text outside Obsidian)
- Syntax: `- [ ] description #todo/<type> [[related page]] 📅 YYYY-MM-DD`; done `- [x] … ✅ YYYY-MM-DD`, dropped `- [x] ~~description~~ ❌ <reason> YYYY-MM-DD` (both done and dropped close the box to `- [x]` so the aggregate query's `not done` excludes them). Every real todo carries a `#todo/<type>` tag.
- Primary store: cross-project / meta todos live in the central `wiki/todos.md` under `## In progress` / `## Backlog`; you may evolve this (e.g. keep project-specific todos on a project page), where completed items stay in place as decision-log context rather than being moved.
- Archive on completion: each ingest sweeps items just marked ✅ / ❌ in the central `wiki/todos.md` into the trailing `## 📦 Done archive` section (one-line conclusion + date), so the primary store only ever holds active items; the sweep touches the central todos.md only.
- View never materialized: "what's on my plate right now" is a Claude session output (the ingest wrap-up list, and "list my todos" on demand), not a fixed section in todos.md. The file is storage only (primary-store sections + `## 📦` archive + an optional Obsidian aggregation query); ask Claude for the board. This is why non-Obsidian setups need no dead query text.
- Inventory digs for evidence: do not judge a todo's state from its checkbox text alone; first read the related project's git log and project memory to verify progress, and cite evidence when marking something done (see ingest D.3 and maintain).
- Aggregation-query pitfall: an Obsidian Tasks aggregation query must carry `tags include #todo` (only items with a `#todo` tag), plus `tags do not include #todo/stale` and `path does not include diaries/`. Filtering by path / stale alone pulls every stray `- [ ]` (migration playbooks, archived files, `- [ ]` examples in docs) into the board; non-todo checkboxes have no tag and are excluded automatically. Put one field per `sort by` line.
