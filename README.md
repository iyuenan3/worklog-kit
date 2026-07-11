# worklog-kit

> 睡前对 Claude 说一句「记录今天」，第二天醒来：日记写好了、wiki 更新了、TODO 盘点了、已经 commit 了。

worklog-kit 是一套**个人项目大脑**的开箱即用模板：用一个「父项目」vault 管住你所有项目的日常动态与长期知识。它是 [project-lifecycle 方法论](https://github.com/iyuenan3/personal-skills/blob/main/project-lifecycle.md) 的官方参考实现。

## 它做什么

- **每晚自动编译日记**：扫描你所有工作发生的地方（本机多目录多硬盘、GitHub / GitLab、远程机器、飞书协调记录），加上你睡前的一句话补充，编译成可复盘的结构化日记
- **知识自动沉淀**：项目动态、决策、踩坑流入 wiki，跨项目可查可互链
- **全程无人值守**：触发即全部输入，任何数据源失败都降级记录、绝不挂起等你回话
- **隐私出厂即紧**：默认私仓 + 公开仓检测拦截 + 凭证隔离 + 飞书默认只记你自己发的消息

## 状态

**pre-alpha，立项阶段（2026-07-11）**，尚不可用。规格见 [PRD.md](PRD.md)。

## 要求

- Claude Code 订阅（macOS / Linux；Windows 仅 WSL 实验性）
- git 与基本终端使用
- 可选：GitHub / GitLab CLI（平台收集器）、飞书 + `@larksuite/cli`（IM 协调源）、Obsidian（推荐查看器）

## License

Apache-2.0
