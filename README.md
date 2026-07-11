# worklog-kit

> 睡前对 Claude 说一句「记录今天」，第二天醒来：日记写好了、wiki 更新了、TODO 盘点了、已经 commit 了。

worklog-kit 是一套**个人项目大脑**的开箱即用模板：用一个「父项目」vault 管住你所有项目的日常动态与长期知识。它是 [project-lifecycle 方法论](https://github.com/iyuenan3/personal-skills/blob/main/project-lifecycle.md) 的官方参考实现，面向**任何 Claude Code 用户**：不预设你的公司环境、IM 工具或语言，一切个人接线皆是配置与连接器。

## 它做什么

- **每晚自动编译日记**：扫描你所有工作发生的地方（本机多目录多硬盘、GitHub / GitLab、远程机器、IM 协调记录），加上你睡前的一句话补充，编译成可复盘的结构化日记
- **知识自动沉淀**：项目动态、决策、踩坑流入 wiki，跨项目可查可互链
- **全程无人值守**：触发即全部输入，任何数据源失败都降级记录、绝不挂起等你回话
- **隐私出厂即紧**：默认私仓 + 公开仓检测拦截 + 凭证隔离 + IM 默认只记你自己发的消息

## 状态

**pre-alpha，立项阶段（2026-07-11）**，尚不可用。规格见 [PRD.md](PRD.md)。

## 要求

- 硬前提：Claude Code 订阅，会 git 与基本终端（macOS / Linux；Windows 仅 WSL 实验性）
- 可选：GitHub / GitLab CLI（平台收集器）、IM 连接器（v0.1 内置飞书 `@larksuite/cli`，接口开放可扩展 Slack 等）、Obsidian（推荐查看器）
- 语言：中文 / English 双 locale 骨架，初始化时选择

## License

Apache-2.0
