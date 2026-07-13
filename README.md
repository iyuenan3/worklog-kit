# worklog-kit

> English: [README.en.md](README.en.md)

> 睡前对 Claude 说一句「记录今天」，第二天醒来：日记写好了、wiki 更新了、TODO 盘点了、已经 commit 了。

worklog-kit 是一套开箱即用的**个人项目大脑**模板：一个「父项目」仓库管住你所有项目的每日动态与长期知识。日记自动编译、知识自动沉淀、全程无人值守，数据永远在你自己的私有 git 仓里。

它是 [project-lifecycle 方法论](docs/methodology.md)的官方参考实现，面向**任何 Claude Code 用户**：不预设你的公司、IM 工具或语言，一切个人差异都是配置与连接器。

## 它做什么

日常使用就是对 Claude 说几句话：

| 你说 | 发生什么 |
|---|---|
| 「记录今天」+ 一句话补充 | 扫描你全部工作现场，编译结构化日记 + 刷新 wiki + 盘点 TODO + commit，无人值守跑完 |
| 「查 X」 | 跨日记与 wiki 检索，答案带出处 |
| 丢个文件「收进 inbox」 | PDF / Word / PPT 转 markdown 入素材库，当晚日记引用；深度消化说一声即可 |
| 「检查」 | 正误检查（契约锚点 / 凭证泄漏 / 断链）+ 体检五项（漂移 / 孤儿 / 分裂 / 膨胀 / TODO 积龄） |
| 「维护 vault」 | 批处理保养：按体检项分类修复（合并 / 归档 / 重链），每类一个 commit |
| 「升级 skill」 | 从上游按 release tag 更新，永不碰你的数据 |
| 「导出」 | 全量转纯 markdown 带走，不依赖任何工具链 |

「工作现场」指哪里？本机多目录多硬盘（嵌套子仓、并列多仓、submodule 各自独立成项）、GitHub、远程机器、IM 协调记录（GitLab 计划中），非 git 的写作 / 设计目录也可声明进来（只记有无动静、不读内容），再加睡前那句 brain-dump 兜底。任何数据源夜里失败都只降级为晨报里的一行，绝不挂起等你回话。

## 快速开始

1. GitHub 点「Use this template」建你自己的仓库，**Visibility 选 Private**
2. 用 Claude Code 打开仓库，说「初始化」：回答「你的工作都发生在哪」，给发现的项目逐个定记录级别
3. 当晚睡前说「记录今天」，然后去睡

> **不要 fork**：公开仓的 fork 无法转私有，你的日记会直接公开。不用 GitHub 托管也行：clone 后自建私有远端。之后请一直保持私有；装有 GitHub CLI（gh）时，init 与每晚 push 前会自动检测兜底。

## 长成你的样子

模板只是第 0 天的形状。**这套系统的设计预期，就是被你和你的 Claude 持续改造**：固定不变的只有极少数契约，其余一切跟着你的用法生长。

| 层 | 目录 | 固定的 | 生长的 |
|---|---|---|---|
| 日记 | `diaries/` | 文件名格式、只追加 | 章节结构随你演化：想加「阅读」「健身」段，直接说 |
| 知识 | `wiki/` | 三处段落锚点 | 项目页、索引、TODO 随你的项目自然长 |
| schema | `worklog.config.yaml` + `AIREADME/` | `schema_version` | 数据源、记录级别、模块开关、一切约定 |

想改什么，对你的 Claude 说就行：

- **「换了新电脑 / 新硬盘 / 新公司」**：config 的 `sources` 加一行，完事
- **「给我做一个周报 skill，每周五汇总本周日记」**：自建 skill 放进 `.claude/skills/` 新目录，从此「写周报」也是一句话的事
- **「我们公司用 Slack」**：IM 连接器接口是开放的（`.claude/skills/worklog-ingest/connectors/README.md`），照飞书参考实现写一个即可

敢放手让它长，因为有三条轨道兜底：

1. **红线极少**：契约锚点、三层所有权、隐私，只此三条（仓内 `CLAUDE.md` 列明），其余全是软性约定
2. **升级不冲突**：`worklog-update` 只同步 kit 自带 skill；你自建的 skill 永不被碰，你改过的 kit skill 升级时逐个展示差异、由你决定覆盖或保留
3. **演化有账本**：结构变了说一声「更新 AIREADME」，改动与理由记进 `AIREADME/DECISIONS.md`，半年后还读得懂当初为什么

用得越久，这个 vault 越不像模板，越像你。

## 隐私（出厂即紧）

- **默认私仓**：装有 GitHub CLI（gh）时，init 与每晚 push 前自动检测 visibility，发现公开立即拦截；未装 gh 无法自动检测，请自行确认仓库私有
- **凭证隔离**：密钥永不入 git（.gitignore 预置 + lint 凭证扫描兜底）
- **IM 最小记录**：默认只记你自己发的消息
- **记录须同意**：每个被发现的项目经你定级（detail / summary / presence / exclude）才会详细记录
- **零遥测**：不回传任何数据，维护者永远看不到你的日记

## 接入 IM（可选）

用 IM 协调工作的话，任何时候说「配置飞书」：向导带你完成官方 lark-cli 安装、扫码授权、挑选要读取的会话、自检试拉。企业租户不允许自建应用时此连接器不可用，跳过即可，其余一切照常。飞书是 IM 连接器接口的首个参考实现，Slack 等按接口可扩展（接口文档：`.claude/skills/worklog-ingest/connectors/README.md`）。

## 状态

**pre-alpha（2026-07-11 立项）**：M1 至 M4 与 M6（vault 记忆维护）已完成，init / ingest / 连接器（GitHub + 飞书）/ import / query / lint / maintain / update / export 全部可用；模板已公开，种子用户试用（M5）进行中。规格见 [docs/dev/PRD.md](docs/dev/PRD.md)，方法论全文见 [docs/methodology.md](docs/methodology.md)。

## 要求

- 硬前提：Claude Code 订阅，会 git 与基本终端（macOS / Linux；Windows 仅 WSL 实验性）
- 基础环境：git ≥ 2.20、python3 ≥ 3.8、bash ≥ 3.2（macOS 自带即满足）
- 可选：GitHub CLI（平台收集器；GitLab 计划中）、IM 连接器（v0.1 内置飞书 `@larksuite/cli`，接口开放可扩展 Slack 等）
- 强烈推荐 Obsidian 作查看器（不装一切照常）：`.obsidian/` 最小配置随模板附带，装上 Tasks 插件即得 TODO 聚合视图（双链图谱是 Obsidian 自带能力，无需插件）；「查 X」的关键词类检索在 Obsidian 运行时会自动改走其 CLI，更快
- 语言：中文 / English 双 locale 骨架，初始化时选择

## Troubleshooting

- **首次运行命令弹权限确认**：Claude Code 会加载仓内 `.claude/settings.json` 的 allow 清单，常用命令不应弹窗；仍弹窗说明该命令模式不在清单里，确认无害后选择「始终允许」，或把对应模式加进 `permissions.allow`
- **某个数据源夜里失败**：这是设计内的常态路径，晨起报告和 `.ingest-status.md` 会写明原因与自救命令，ingest 不会因此挂起等你
- **worktree / bare 仓布局**：worktree 检出不独立成项（commit 经主仓捕获，主仓不在扫描目录内时晨报会提示补目录）；纯 bare 仓暂不支持自动发现，在扫描目录内放一份普通检出即可
- **一晚 ingest 花多少额度**：普通规模（十来个项目）约等于一次简短的交互编码会话；重度配置（上百仓 / 多个 IM 群）按比例增加。撞到订阅限流时本次运行会中断，已完成部分已 commit，锁文件超 2 小时自动按僵尸锁处理，次日说「补充昨天」即可续上

## License

Apache-2.0
