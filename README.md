# worklog-kit

> English: [README.en.md](README.en.md)

> 睡前对 Claude 说一句「记录今天」，第二天醒来：日记写好了、wiki 更新了、TODO 盘点了、已经 commit 了。

worklog-kit 是一套**个人项目大脑**的开箱即用模板：用一个「父项目」vault 管住你所有项目的日常动态与长期知识。它是 [project-lifecycle 方法论](docs/methodology.md) 的官方参考实现，面向**任何 Claude Code 用户**：不预设你的公司环境、IM 工具或语言，一切个人接线皆是配置与连接器。

## 它做什么

- **每晚自动编译日记**：扫描你所有工作发生的地方（本机多目录多硬盘、GitHub、远程机器、IM 协调记录；GitLab 计划中），加上你睡前的一句话补充，编译成可复盘的结构化日记
- **知识自动沉淀**：项目动态、决策、踩坑流入 wiki，跨项目可查可互链
- **全程无人值守**：触发即全部输入，任何数据源失败都降级记录、绝不挂起等你回话
- **隐私出厂即紧**：默认私仓 + 公开仓检测拦截 + 凭证隔离 + IM 默认只记你自己发的消息；每个被发现的项目须经你定级授权后才详细记录
- **数据永远是你的**：worklog-export 随时把全部内容导出为不依赖任何工具链的纯 markdown

## 快速开始（pre-alpha）

1. GitHub「Use this template」建你自己的**私有**仓库（或 clone 后自建私有远端）
2. 用 Claude Code 打开仓库，说「初始化」（触发 `/worklog-init`）
3. 按引导完成：环境预检 → 回答「你的工作都发生在哪」→ 项目扫描预览与定级 → 全局 skill 安装
4. 每晚睡前说「记录今天」+ 一句话补充，然后去睡

## 状态

**pre-alpha（2026-07-11 立项）**：M1 至 M4 已完成，init / ingest / 连接器（GitHub + 飞书）/ import / query / lint / update / export 全部可用；当前处于 M5（种子用户试用与发布准备）。规格见 [docs/dev/PRD.md](docs/dev/PRD.md)，方法论全文见 [docs/methodology.md](docs/methodology.md)。

## 要求

- 硬前提：Claude Code 订阅，会 git 与基本终端（macOS / Linux；Windows 仅 WSL 实验性）
- 基础环境：git ≥ 2.20、python3 ≥ 3.8、bash ≥ 3.2（macOS 自带即满足）
- 可选：GitHub CLI（平台收集器；GitLab 计划中）、IM 连接器（v0.1 内置飞书 `@larksuite/cli`，接口开放可扩展 Slack 等）、Obsidian（推荐查看器）
- 语言：中文 / English 双 locale 骨架，初始化时选择

## Troubleshooting

- **首次运行命令弹权限确认**：Claude Code 会加载仓内 `.claude/settings.json` 的 allow 清单，常用命令不应弹窗；仍弹窗说明该命令模式不在清单里，确认无害后选择「始终允许」，或把对应模式加进 `permissions.allow`
- **某个数据源夜里失败**：这是设计内的常态路径，晨起报告和 `.ingest-status.md` 会写明原因与自救命令，ingest 不会因此挂起等你

## License

Apache-2.0
