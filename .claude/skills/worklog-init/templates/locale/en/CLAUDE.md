# CLAUDE.md · my worklog (router)

> This repo = your "parent project" vault: a personal knowledge base + work diary system on a three-layer architecture (diary append-only / wiki LLM-maintained / schema co-evolved by human + LLM), powered by [worklog-kit](https://github.com/iyuenan3/worklog-kit).
> Configuration lives in `worklog.config.yaml` (credentials only in `worklog.config.local.yaml`, gitignored). Full methodology: `docs/methodology.md`.

## Routing (trigger → behavior)

| Trigger / task | Behavior | skill |
|---|---|---|
| "initialize / init / setup" | Initialize the vault: preflight + config + project leveling + global skill install | worklog-init |
| "log today / yesterday / YYYY-MM-DD / append today / amend the diary / backfill N days" | Unattended ingest: scan sources, compile the diary, refresh wiki, review todos, commit | worklog-ingest |
| Drop a file / "into inbox / import this" | Convert material to markdown into `inbox/` | worklog-import |
| "set up Feishu / connect IM" | IM connector install and auth wizard | feishu-setup |
| "look up X" | Search across diaries + wiki (read-only, cited answers) | worklog-query |
| "check / lint" | Contract anchors / credentials / broken links / frontmatter plus writing gates (punctuation gate zh only, date gate runs for zh and en) | worklog-lint |
| "upgrade skills" | Pull new versions from upstream by release tag (touches `.claude/skills/` only, never your data) | worklog-update |
| "export / move out" | Export everything as toolchain-free plain markdown (exit path) | worklog-export |

> Day boundary: 00:00 until config `day_boundary` (default 07:00) belongs to the previous day. Timezone per config `timezone`.

## Hard rules

- **Three-layer ownership**: `diaries/` is append-only, never rewrite history; `wiki/` is maintained by ingest, keep the section anchors when editing by hand (index's three headings / log's anchor comment / todos' section headings); schema evolution goes into `AIREADME/` (rationale into DECISIONS).
- **Privacy**: this repo must stay **private** (ingest verifies visibility before every push); credentials / private keys never enter git (.gitignore preloaded); IM sources record only your own messages by default.
- `inbox/` is the raw-material dropbox: humans put things in, AI digests them; archive or delete once digested.

## Maintenance & self-development

- Structural evolution is the design intent: apart from the anchors and contract files above, let everything grow with your usage; when it changes, run `/aireadme` to update `AIREADME/` (rationale into DECISIONS).
- **Continuous self-development of this vault is welcome**: new diary sections, new wiki structures, and skills of your own (weekly reports / reviews / whatever your workflow needs) are all by design, not a deviation. Put your own skills in `.claude/skills/<new-dir>/`; worklog-update never touches locally-added skills. Modifying kit-shipped skills is fine too: upgrades show a per-skill diff and you decide to overwrite or keep.
- New project / device / IM: add one entry under `sources` in `worklog.config.yaml`; when unsure about a level, start with `presence`.

---
> Developing worklog-kit itself (rather than using this vault)? Read `docs/dev/`. As a vault user you can ignore this line (init removes it together with the dev docs).
