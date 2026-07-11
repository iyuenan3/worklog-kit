# ARCHITECTURE

## Three layers

| Layer | Directory | Ownership |
|---|---|---|
| Diary | `diaries/` | append-only (ingest writes, humans read and append) |
| Knowledge | `wiki/` | LLM-maintained (ingest updates; humans may edit, keep anchors) |
| Schema | `AIREADME/` + `worklog.config.yaml` | co-evolved by human + LLM |

## Data flow

sources (declared in config: local multi-root / hosting platforms / remote machines / IM / brain-dump) → nightly ingest → `diaries/YYYY-MM-DD.md` + three wiki refreshes (index summary and tables / log append / project pages) + todo review → commit + push (visibility check before push).

`inbox/` ← humans drop raw material (worklog-import converts to markdown) → ingest references the day's additions; archive after digestion into the wiki.

## Do not touch
- The three headings of `wiki/index.md`, the anchor comment of `wiki/log.md`, the section headings of `wiki/todos.md` (ingest write anchors; if changed, ingest falls back to appending and warns in the morning report)
- `schema_version` in `worklog.config.yaml` is managed by worklog-update; do not edit by hand
