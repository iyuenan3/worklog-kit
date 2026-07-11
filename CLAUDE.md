# CLAUDE.md · worklog-kit（router）

> worklog-kit = personal-skills `project-lifecycle.md` 方法论的官方参考实现：把维护者私有 worklog 工作流（三层架构 + 睡前无人值守 ingest）产品化，给有 Claude Code 订阅、用飞书的用户 clone 即用。
> **真相源是 `PRD.md`**（需求 + 工程规格 + 审计收敛结论），本文件只放路由与红线。

## 当前阶段

- 2026-07-11 立项（最小骨架：CLAUDE.md + PRD.md + README.md + git init）。
- 下一步按 PRD §15 里程碑推进：M1 模板骨架 → M2 ingest 重写 → M3 连接器 → M4 收尾 → M5 pilot。
- 开工时先用 `/aireadme` 建本仓 AIREADME/。

## 路由

| 任务 | 读 |
|---|---|
| 任何需求 / 规格 / 契约问题 | `PRD.md`（§5 冻结契约、§8 ingest 重写规格、§9 安全隐私） |
| 方法论背景 | `../personal-skills/project-lifecycle.md` |
| 私有版 ingest 参考实现 | `../worklog/.claude/skills/worklog-ingest/`（只读参考，见下红线） |

## 红线

- **本仓一切内容默认将来公开**：任何文件（含文档、示例、注释、commit message）不得含维护者个人信息、客户 / 雇主名、具名设备、IM 群坐标、真实同事称呼。从私有 worklog 借鉴实现时只搬骨架不搬数据。公开发布前须过对抗式泄漏审计（含 git 全历史）。
- 冻结契约（PRD §5）改动必须同步 PRD，并评估对已铺出去的用户 vault 的兼容性。
- 不 vendor aireadme / stash / pitfalls 三件套（上游 personal-skills，锁 release tag），理由见 PRD §4.2。
- 中文文案用中文全角标点，绝不使用破折号（全局规范）。

## 惯例

- git 直接提 `main`。
- 目录命名遵循契约：`diaries/`（复数）、`wiki/`、`inbox/`。
