# CLAUDE.md · worklog-kit（router）

> worklog-kit = personal-skills `project-lifecycle.md` 方法论的官方参考实现：把源自维护者私有 worklog 的工作流（三层架构 + 睡前无人值守 ingest）产品化成**任何 Claude Code 用户拿来即用**的通用开源项目。
> **真相源是 `PRD.md`**（需求 + 工程规格 + 审计收敛结论），本文件只放路由与红线。

## 当前阶段

- 2026-07-11 立项（最小骨架）；同日 PRD 迭代至 v0.3（v0.2 通用化修正：任何人可用、IM 连接器化、三件套 vendor 快照、仓根即模板；v0.3 项目发现与记录同意：发现 ≠ 记录、四级定级。修订记录见 PRD 文末）。
- 下一步按 PRD §15 里程碑推进：M1 模板骨架 → M2 ingest 重写 → M3 连接器 → M4 收尾 → M5 pilot 与发布。
- **M1 起仓根即用户 vault 模板**：本文件将被面向用户的产品 router 替换，开发文档（含 PRD）迁入 `docs/dev/`。开工时先用 `/aireadme` 建本仓 AIREADME/。

## 路由

| 任务 | 读 |
|---|---|
| 任何需求 / 规格 / 契约问题 | `PRD.md`（§5 冻结契约、§6.3 IM 连接器接口、§8 ingest 重写规格、§9 安全隐私） |
| 方法论背景 | `../personal-skills/project-lifecycle.md` |
| 私有版 ingest 参考实现 | `../worklog/.claude/skills/worklog-ingest/`（仅开发期本机参考，见下红线；此路径不得写进任何产品件） |

## 红线

- **本仓一切内容默认将来公开**：任何文件（含文档、示例、注释、commit message）不得含维护者个人信息、客户 / 雇主名、具名设备、IM 群坐标、真实同事称呼。从私有 worklog 借鉴实现时只搬骨架不搬数据。公开发布前须过对抗式泄漏审计（含 git 全历史）。
- **通用性红线**（PRD 原则 2）：核心流程不得引入特定 IM / 托管平台 / 语言 / 公司环境假设；特定能力一律下沉为连接器或 locale 模板。评审任何改动先问一句：一个用 Slack、说英文、不在中国的陌生用户拿到后还能用吗。
- 冻结契约（PRD §5）改动必须同步 PRD，并评估对已铺出去的用户 vault 的兼容性。
- 三件套（aireadme / stash / pitfalls）是 vendor 快照，只经 `scripts/sync-upstream.sh` 从 personal-skills release tag 单向同步，不手改快照内容（改上游再同步）。
- 中文文案用中文全角标点，绝不使用破折号（全局规范）。

## 惯例

- git 直接提 `main`。
- 目录命名遵循契约：`diaries/`（复数）、`wiki/`、`inbox/`。
