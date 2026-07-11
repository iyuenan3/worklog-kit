# RELATIONS

## Outbound dependencies
- **worklog-kit** (upstream, https://github.com/iyuenan3/worklog-kit): source of skill updates; worklog-update syncs `.claude/skills/` only and never touches vault data
- **My subprojects**: scanned via `sources` in `worklog.config.yaml`; each keeps its own source of truth in its own `AIREADME/` (if any)

## Inbound (who depends on me)
- (none: this vault is not consumed by other projects; if a consumer appears, e.g. a homepage builder reading `wiki/projects/`, define the contract in SPEC and register it here)

## Shared foundations
- (none)
