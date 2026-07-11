# Getting started (this file is gitignored; delete after reading)

Initialization is done. The next three days are a break-in period: diary quality improves day by day. That is expected.

## Tonight (first capture)

Before bed, tell Claude Code "log today", **ideally with two or three sentences about what you did**, e.g.:

> Log today. Morning was mostly the login flow of project X, afternoon a requirements review, nothing in the evening.

Your message is the entire input. Send it and go to sleep: ingest runs fully unattended, and any failing source gets one line in the report instead of blocking.

## Tomorrow morning (first review)

1. Read your first diary under `diaries/`
2. Anything wrong? Just say "update the diary: change XXX to YYY"
3. Skim the morning report: any skipped sources, any "new projects awaiting a level"

## Common first-run issues

- **A project was not scanned** → check that `sources.roots` in `worklog.config.yaml` covers its path
- **Empty timeline** → no commits that day; narrate the work in your brain-dump instead
- **A new project shows only a count** → that is the safe default (presence level); say "promote project X to detail"
- **Keep a project out of the diary entirely** → drop an empty `.worklogignore` file in its root
- **Projects organized via symlinks** → discovery does not follow symlinks; add the real paths to `sources.roots`

## Three habits

1. A one-line brain-dump before bed (scanning has blind spots; your sentence is the strongest source)
2. Throw new material into `inbox/` instead of editing the wiki directly (let ingest digest it)
3. Evolve the wiki structure freely; afterwards ask AIREADME to record why
