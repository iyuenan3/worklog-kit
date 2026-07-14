# TODO

> Primary store: active todos live in the `## In progress` / `## Backlog` sections below, in Obsidian Tasks syntax. Outside Obsidian the `tasks` code block renders as plain text, which does not affect the records themselves.
> Syntax: `- [ ] description #todo/<type> [[related page]] 📅 YYYY-MM-DD` (every real todo carries a `#todo/<type>` tag; the aggregated view keys off it).
> The file is storage only; the "what's on my plate right now" view is not hard-coded here. Ask Claude to compute it on demand (ingest also prints an unfinished-items list on wrap-up).
> Each ingest reviews todos: read git log and project memory to verify progress, then judge four states (done + evidence, dropped, split, deferred); completed items are swept into the archive section below, clearly stalled ones get `#todo/stale`.

## In progress

## Backlog

## 📦 Done archive

> Ingest sweeps items just marked ✅ / ❌ from the primary store above into here, keeping a one-line conclusion + date (full context lives in that day's diary).

## Aggregated view (optional, requires the Obsidian Tasks plugin)

```tasks
not done
tags include #todo
tags do not include #todo/stale
path does not include diaries/
sort by due
```
