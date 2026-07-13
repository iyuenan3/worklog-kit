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
- Todos use Obsidian Tasks syntax in the sections of `wiki/todos.md` (valid outside Obsidian too, see that file's header note)
