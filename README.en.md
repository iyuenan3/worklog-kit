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

1. GitHub "Use this template" → create your repo with **visibility set to Private, and do not fork** (a fork of a public repo cannot be made private, so your diary would be public; not hosting on GitHub is fine too: clone and set up your own private remote). Keep it private from then on; init and every nightly push run an automatic visibility check as a backstop
2. Open it in Claude Code, say "initialize" (`/worklog-init`)
3. Follow the wizard: preflight → "where does your work happen" → project discovery and leveling → global skill install
4. Before bed: "log today" plus a sentence or two, then go to sleep

## Connecting an IM (optional)

If you coordinate work over an IM, say "set up Feishu" to Claude at any time: the `feishu-setup` wizard walks you through installing the official lark-cli, QR-code auth, picking the chats to read, writing the config, and a self-test pull. Only your own messages are recorded by default. If your company tenant does not allow self-built apps, this connector is unavailable; just skip it, everything else works. Feishu is the first reference implementation of the IM connector interface; Slack and others can be added per `.claude/skills/worklog-ingest/connectors/README.md`.

## It grows into your shape

The template is a starting point, and everyone works differently: **this vault is meant to be continuously developed by you and your Claude**. Reshape diary sections, evolve the wiki structure, add your own skills under `.claude/skills/` (weekly reports, monthly reviews, whatever your workflow needs); that is design intent, not going off-road. Two rails keep it safe: first, the only hard rules are the contract anchors, three-layer ownership, and privacy (see `CLAUDE.md` in the repo), everything else grows with use; second, upgrades never collide, since `worklog-update` only syncs kit-shipped skills and never touches skills you created (if you modified a kit-shipped skill, the upgrade shows a per-skill diff and you decide to overwrite or keep). After evolving, say "update AIREADME" and the rationale lands in `AIREADME/DECISIONS.md`, still legible six months later.

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
- **How much quota does a night cost**: a typical setup (a dozen projects) is comparable to one short interactive coding session; heavy setups (100+ repos, several IM chats) scale proportionally. If you hit your subscription rate limit mid-run, the run stops, finished parts are already committed, the lock file goes stale after 2 hours, and saying "append yesterday" the next day picks things up

## License

Apache-2.0
