# CLAUDE.md · my worklog (router)

> This repo = your "parent project" vault: a personal knowledge base + work diary system on a three-layer architecture (diary append-only / wiki LLM-maintained / schema co-evolved by human + LLM), powered by [worklog-kit](https://github.com/iyuenan3/worklog-kit).
> Configuration lives in `worklog.config.yaml` (credentials only in `worklog.config.local.yaml`, gitignored). Full methodology: `docs/methodology.md`.

## Routing (trigger → behavior)

| Trigger / task | Behavior | skill |
|---|---|---|
| "initialize / init / setup" | Initialize the vault: preflight + config + project leveling + global skill install | worklog-init |
| "log today / yesterday / YYYY-MM-DD / append today / amend the diary / backfill N days" | Unattended ingest: scan sources, compile the diary, refresh wiki, review todos, commit | worklog-ingest |
| Drop a file / "into inbox" | Convert material to markdown into `inbox/` | worklog-import (coming soon) |
| "look up X" | Search across diaries + wiki | worklog-query (coming soon) |
| "check / lint" | Broken links / frontmatter / credential scan | worklog-lint (coming soon) |
| "upgrade skills" | Pull new skill versions from upstream (touches `.claude/skills/` only, never your data) | worklog-update (coming soon) |

> Day boundary: 00:00 until config `day_boundary` (default 07:00) belongs to the previous day. Timezone per config `timezone`.

## Hard rules

- **Three-layer ownership**: `diaries/` is append-only, never rewrite history; `wiki/` is maintained by ingest, keep the section anchors when editing by hand (index's three headings / log's anchor comment / todos' section headings); schema evolution goes into `AIREADME/` (rationale into DECISIONS).
- **Privacy**: this repo must stay **private** (ingest verifies visibility before every push); credentials / private keys never enter git (.gitignore preloaded); IM sources record only your own messages by default.
- `inbox/` is the raw-material dropbox: humans put things in, AI digests them; archive or delete once digested.

## Maintenance

- Structural evolution is the design intent: apart from the anchors and contract files above, let everything grow with your usage; when it changes, run `/aireadme` to update `AIREADME/`.
- New project / device / IM: add one entry under `sources` in `worklog.config.yaml`; when unsure about a level, start with `presence`.
