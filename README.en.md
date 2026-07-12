# worklog-kit

> 中文版：[README.md](README.md)

> Tell Claude "log today" before bed. Wake up to a written diary, an updated wiki, a reviewed todo list, and a commit.

worklog-kit is a turn-key template for a **personal project brain**: one "parent project" repo that holds the daily activity and long-term knowledge of all your projects. The diary compiles itself, knowledge accumulates on its own, everything runs unattended, and the data never leaves your own private git repo.

It is the official reference implementation of the [project-lifecycle methodology](docs/methodology.md), built for **any Claude Code user**: no assumptions about your company, IM tool, or language; every personal difference is config or a connector.

## What it does

Day-to-day use is a few sentences to Claude:

| You say | What happens |
|---|---|
| "log today" plus a one-line brain-dump | Scans everywhere your work happens, compiles a structured diary, refreshes the wiki, reviews todos, commits; fully unattended |
| "look up X" | Searches across diaries and wiki, answers with citations |
| Drop a file, "into inbox" | PDF / Word / PPT converted to markdown; that night's diary references it, deep digestion on request |
| "check" | Correctness checks (contract anchors / credential leaks / broken links) plus five checkup metrics (drift / orphans / splits / bloat / stale todos) |
| "maintain vault" | Batch upkeep: repairs checkup items by corruption type (merge / archive / relink), one commit per type |
| "upgrade skills" | Updates from upstream by release tag, never touches your data |
| "export" | Everything out as toolchain-free plain markdown |

Where is "everywhere your work happens"? Local multi-root and multi-disk, GitHub, remote machines, IM coordination (GitLab planned), plus that bedtime brain-dump as the catch-all. Any source failing overnight degrades to one line in the morning report; nothing ever blocks waiting for you.

## Quick start

1. GitHub "Use this template" → create your own repo, **visibility set to Private**
2. Open it in Claude Code, say "initialize": answer "where does your work happen" and set a recording level for each discovered project
3. Before bed, say "log today", then go to sleep

> **Do not fork**: a fork of a public repo cannot be made private, so your diary would be public. Not hosting on GitHub is fine too: clone and set up your own private remote. Keep the repo private from then on; with the GitHub CLI (gh) installed, init and every nightly push run an automatic visibility check as a backstop.

## It grows into your shape

The template is only day zero. **This system is designed to be continuously reshaped by you and your Claude**: only a handful of contracts stay fixed, and everything else grows with how you actually work.

| Layer | Directory | Fixed | Grows |
|---|---|---|---|
| Diary | `diaries/` | Filename format, append-only | Section structure evolves with you: want a "Reading" or "Fitness" section, just say so |
| Knowledge | `wiki/` | Three section anchors | Project pages, index, and todos grow with your projects |
| Schema | `worklog.config.yaml` + `AIREADME/` | `schema_version` | Sources, recording levels, module switches, every convention |

Want something changed? Tell your Claude:

- **"New laptop / new disk / new job"**: add one line under `sources` in the config, done
- **"Build me a weekly-report skill that digests this week's diaries every Friday"**: your own skill goes into a new directory under `.claude/skills/`, and "weekly report" becomes a one-liner from then on
- **"My team uses Slack"**: the IM connector interface is open (`.claude/skills/worklog-ingest/connectors/README.md`); write one modeled on the Feishu reference implementation

You can let it grow because three rails keep it safe:

1. **Minimal hard rules**: contract anchors, three-layer ownership, privacy; those three only (listed in the repo's `CLAUDE.md`), everything else is soft convention
2. **Upgrades never collide**: `worklog-update` only syncs kit-shipped skills; skills you created are never touched, and kit skills you modified show a per-skill diff at upgrade time for you to overwrite or keep
3. **Evolution keeps a ledger**: after a structural change, say "update AIREADME" and the change plus rationale land in `AIREADME/DECISIONS.md`, still legible six months later

The longer you use it, the less it looks like a template and the more it looks like you.

## Privacy (tight out of the box)

- **Private by default**: with the GitHub CLI (gh) installed, init and every nightly push verify repo visibility and block if public; without gh there is no automatic check, so confirm the repo is private yourself
- **Credential isolation**: keys never enter git (.gitignore preloaded, lint credential scan as backstop)
- **Minimal IM recording**: only your own messages by default
- **Consent before recording**: every discovered project is recorded in detail only after you set its level (detail / summary / presence / exclude)
- **Zero telemetry**: nothing phones home; the maintainer can never see your diary

## Connecting an IM (optional)

If you coordinate work over an IM, say "set up Feishu" at any time: the wizard walks you through installing the official lark-cli, QR-code auth, picking the chats to read, and a self-test pull. If your company tenant does not allow self-built apps, this connector is unavailable; skip it, everything else works. Feishu is the first reference implementation of the IM connector interface; Slack and others can be added per the interface doc at `.claude/skills/worklog-ingest/connectors/README.md`.

## Status

**pre-alpha (started 2026-07-11)**: M1 through M4 plus M6 (vault memory maintenance) are done; init / ingest / connectors (GitHub + Feishu) / import / query / lint / maintain / update / export all work. The template is public; seed-user pilot (M5) is in progress. Spec: [docs/dev/PRD.md](docs/dev/PRD.md); methodology: [docs/methodology.md](docs/methodology.md).

## Requirements

- Hard requirements: a Claude Code subscription, basic git and terminal use (macOS / Linux; Windows via WSL, experimental)
- Base environment: git ≥ 2.20, python3 ≥ 3.8, bash ≥ 3.2 (stock macOS qualifies)
- Optional: GitHub CLI (platform collector; GitLab planned), an IM connector (Feishu via the official `@larksuite/cli` ships in v0.1; the interface is open for Slack and others)
- Obsidian is strongly recommended as the viewer (everything works without it): a minimal `.obsidian/` config ships with the template, so installing the Tasks plugin gets you the todo dashboard (the backlink graph is built into Obsidian itself, no plugin needed); keyword searches in "look up X" automatically switch to the Obsidian CLI when the app is running, which is faster
- Language: zh / en skeleton locales, chosen at init

## Troubleshooting

- **Permission prompts on first run**: Claude Code loads the `.claude/settings.json` allowlist in this repo; most commands should not prompt. If one does, it is not on the list; choose "always allow" or add the pattern to `permissions.allow`
- **A source failed overnight**: that is a designed-for path, not an outage. The morning report and `.ingest-status.md` state the reason and the fix command; ingest never blocks waiting for you
- **How much quota does a night cost**: a typical setup (a dozen projects) is comparable to one short interactive coding session; heavy setups (100+ repos, several IM chats) scale proportionally. If you hit your subscription rate limit mid-run, the run stops, finished parts are already committed, the lock file goes stale after 2 hours, and saying "append yesterday" the next day picks things up

## License

Apache-2.0
