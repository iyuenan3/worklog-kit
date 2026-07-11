# worklog-kit

> 中文版：[README.md](README.md)

> Tell Claude "log today" before bed. Wake up to a written diary, an updated wiki, a reviewed todo list, and a commit.

worklog-kit is a turn-key template for a **personal project brain**: one "parent project" vault that holds the daily activity and long-term knowledge of all your projects. It is the official reference implementation of the [project-lifecycle methodology](docs/methodology.md), built for **any Claude Code user**: no assumptions about your company, IM tool, or language; every personal wire is config or a connector.

## What it does

- **Compiles your diary nightly, unattended**: scans everywhere your work happens (local multi-root and multi-disk, GitHub, remote machines, IM coordination; GitLab planned), adds your one-line brain-dump, and writes a structured, reviewable diary
- **Knowledge settles automatically**: project activity, decisions, and lessons flow into a wiki, cross-linked and queryable
- **Never blocks**: your trigger message is the entire input; any failing source degrades to one line in the morning report
- **Privacy-tight out of the box**: private repo enforced (visibility check before every push), credential isolation, IM sources record only your own messages by default, and every discovered project needs your consent level before detailed recording
- **Your data stays yours**: worklog-export turns everything into toolchain-free plain markdown at any time

## Quick start (pre-alpha)

1. GitHub "Use this template" → create your **private** repo
2. Open it in Claude Code, say "initialize" (`/worklog-init`)
3. Follow the wizard: preflight → "where does your work happen" → project discovery and leveling → global skill install
4. Before bed: "log today" plus a sentence or two, then go to sleep

## Status

**pre-alpha (started 2026-07-11)**: M1 through M4 are done; init / ingest / connectors (GitHub + Feishu) / import / query / lint / update / export all work. Currently in M5 (seed-user pilot and release preparation). Spec: [docs/dev/PRD.md](docs/dev/PRD.md); methodology: [docs/methodology.md](docs/methodology.md).

## Requirements

- Hard requirements: a Claude Code subscription, basic git and terminal use (macOS / Linux; Windows via WSL, experimental)
- Base environment: git ≥ 2.20, python3 ≥ 3.8, bash ≥ 3.2 (stock macOS qualifies)
- Optional: GitHub CLI (platform collector; GitLab planned), an IM connector (Feishu via the official `@larksuite/cli` ships in v0.1; the interface is open for Slack and others), Obsidian (recommended viewer)
- Language: zh / en skeleton locales, chosen at init

## Troubleshooting

- **Permission prompts on first run**: Claude Code loads the `.claude/settings.json` allowlist in this repo; most commands should not prompt. If one does, it is not on the list; choose "always allow" or add the pattern to `permissions.allow`
- **A source failed overnight**: that is a designed-for path, not an outage. The morning report and `.ingest-status.md` state the reason and the fix command; ingest never blocks waiting for you

## License

Apache-2.0
