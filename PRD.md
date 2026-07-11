# PRD · worklog-kit

> 立项：2026-07-11（周六）｜状态：v0.2 调优中
> 本文档是产品需求 + 工程规格的单一真相源，由四轮孵化讨论 + 一轮 112 条多视角设计审计（4 路并行审计 97 条 + 完整性补漏 15 条）收敛而来，调优阶段直接修订本文档。修订记录见文末。

---

## 1. 背景与定位

worklog-kit 是 [personal-skills](https://github.com/iyuenan3/personal-skills) 中 `project-lifecycle.md` 方法论的**官方参考实现**：用一个「父项目」当大脑，管住一群项目从想法到退役的全生命周期。

它把源自维护者私有 worklog 的工作流（Karpathy LLM Wiki 三层架构 + 睡前无人值守 ingest + 跨项目集体记忆）产品化成**任何人拿来即可使用的通用开源项目**：不预设使用者是谁、在哪家公司、用什么 IM、说什么语言。核心命题一句话：**把「接线」变成「配置」**。可复制的是方法论与工作流骨架（三层所有权、无人值守铁律、默认值表机制、提纯阶梯）；一切个人接线（扫哪些目录、哪台远程机、哪个 IM、哪种语言）都以配置与连接器的形式存在，核心流程零特定假设。

## 2. 目标用户

**硬前提只有两条**：有 Claude Code 订阅；会 git 与基本终端操作。除此之外不预设任何环境。

**首批种子用户画像**（决定 v0.1 连接器与 locale 的优先级，但不构成产品前提）：日常工作用 Claude + Codex、沟通用飞书、中文写作。

平台：macOS 为主，Linux 兼容；Windows 原生不支持，WSL 标注实验性。

## 3. 产品原则

1. **clone 即用**：单仓模板，skill 内嵌 `.claude/skills/`，初始化一次当晚可跑
2. **通用性红线**：核心流程不得含任何特定 IM / 托管平台 / 语言 / 公司环境假设；特定能力一律下沉为连接器（§6.3）或 locale 模板（§5）
3. **冻结契约最小但完整**：skill 只依赖契约清单（§5），其余全部软性，鼓励用户像维护者一样自行演化 schema；产品版 schema 从 v0.1 的简洁度起步，不替用户预演化
4. **每个数据源都可失败**：不可达、鉴权过期、未挂载都是常态路径，降级记录一句继续跑，绝不挂起
5. **无人值守铁律**：触发消息即全部输入，永不阻塞提问，一口气跑到 commit
6. **隐私出厂即紧**：默认私仓 + 公开检测 + 凭证隔离 + IM 最小记录，是默认行为不是文档建议
7. **冷启动即有内容**：第一晚就能看到成型的日记和非空的 wiki
8. **汇流口优先**：数据采集不追着设备跑，优先扫 git 远端 / IM / brain-dump 三个天然汇流口

## 4. 形态与仓库关系

### 4.1 仓根即模板（开发件与产品件分离）

**仓库根目录就是用户的 vault 模板**：用户 GitHub「Use this template」建私仓（或 clone）后，打开即是自己的 vault，根 CLAUDE.md 是面向用户的 vault router（产品件）。kit 自身的开发文档（本 PRD、设计审计、贡献指南）隔离在 `docs/dev/`，`worklog-init` 实例化时提供一键移除；开发期路由同样收在 `docs/dev/`，绝不占用产品件位置。

```
worklog-kit/                      # 仓根 = 用户 vault 模板
├── README.md                     # 产品叙事（project-lifecycle 简版 + 链接完整版）
├── CLAUDE.md                     # vault router（产品件，面向使用者）
├── AGENTS.md                     # 指向 CLAUDE.md（防 Codex 打开 vault 时偏离约定）
├── AIREADME/                     # 极简预置（aireadme skill 可维护）
├── worklog.config.yaml           # 入 git：数据源 / 扫描根 / 时区 / locale / 模块开关（无任何凭证）
├── worklog.config.local.yaml     # 不入 git：敏感字段（.gitignore 预置）
├── .claude/settings.json         # 权限 allow 清单（无人值守前提，不开 bypass）
├── .gitignore                    # 预置：状态文件 / 密钥类 / Obsidian 工作区
├── diaries/                      # 日记层（只追加）
├── wiki/                         # 知识层（LLM 维护）：index.md + log.md + todos.md + projects/
├── inbox/                        # 素材收件箱：人放原料、AI 消化
├── docs/dev/                     # kit 开发文档（PRD / 审计 / CONTRIBUTING），init 可一键移除
└── .claude/skills/
    ├── worklog-init/             # 初始化：环境预检 + config 生成 + 三件套全局安装 + 冷启动
    ├── worklog-ingest/           # config 驱动通用版（核心工程，重写非删改）
    ├── worklog-import/           # markitdown 素材摄入（init 存量迁移复用）
    ├── feishu-setup/             # IM 连接器接口（§6.3）的首个参考实现
    ├── worklog-query/            # 「查 X」显式化
    ├── worklog-lint/             # 断链 / frontmatter / 凭证扫描（标点门为中文 locale 可选项）
    ├── worklog-update/           # 从 upstream 拉 skill 新版（安全边界见 §12）
    ├── aireadme/                 # vendor 快照（见 §4.2）
    ├── stash/                    # vendor 快照
    └── pitfalls/                 # vendor 快照
```

### 4.2 全局三件套：vendor 固定版本快照（v0.2 修正）

- kit **随模板分发三件套（aireadme / stash / pitfalls）的固定版本快照**，`worklog-init` 把它们从 vault 内 cp 到 `~/.claude/skills/` 全局安装（已存在则比对提示覆盖 / 跳过），**全程无运行时网络拉取**
- 修正理由：v0.1 曾定「不 vendor、init 时从 personal-skills 在线拉取」以省维护者同步成本；画像升级为「任何人」后权衡反转，通用产品必须自包含（任意用户的网络环境、上游仓的存续与命名都不可控），维护者同步成本改由 `scripts/sync-upstream.sh`（单向，从 personal-skills 指定 tag 同步 + 版本戳）+ CI drift 提醒覆盖
- personal-skills 仍是三件套的 canonical 上游（打 release tag），kit 快照锁 tag；`project-lifecycle.md` 留在 personal-skills 作完整方法论，kit README 写简版叙事并链接
- pitfalls「高危活前先查」全局纪律行仍**经用户确认后**追加进用户 `~/.claude/CLAUDE.md`（追加前检查该行是否已存在，绝不覆盖已有内容）
- personal-skills README 中 worklog-ingest 条目从「不建议直接使用」改为指向 kit（发布时同步）

## 5. 冻结契约（v0.1）

skill 只依赖以下各项，模板全部预置，`worklog-update` 永不触碰其中的用户数据。**骨架文件按 locale 模板实例化**（v0.1 提供 zh / en 两套，init 按 config `language` 选择；表头、标题、预置文案属 locale 模板，目录名与文件名跨 locale 不变）：

1. 日记文件：`diaries/YYYY-MM-DD.md`（目录名定为 `diaries/` 复数，与方法论源头一致）
2. wiki 骨架四件（ingest 硬依赖，缺一首晚即失败）：
   - `wiki/index.md`：预置头部「最后更新」段 + 项目表 + 日记表的空表格结构（含头部摘要封顶规则，默认保留最近 3 天，可配）
   - `wiki/log.md`：append-only 操作日志（按年轮转防 Read 截断，`log-YYYY.md`）
   - `wiki/todos.md`：TODO 主存储（Obsidian Tasks 语法，非 Obsidian 环境优雅降级为普通 markdown）
   - `wiki/projects/`：项目页目录；项目页 frontmatter schema（`last_updated` / `source_count` / `diaries[]`）入契约
3. `inbox/` 目录存在
4. `worklog.config.yaml`：schema 含 `schema_version` 字段（升级迁移依据）
5. 错误兜底：非致命错误不中断，已完成部分先 commit，卡点写 `.ingest-status.md`（.gitignore 内）
6. 并发锁：ingest 启动建 `.ingest.lock`（PID + 时间戳），存在即报错退出，超 2 小时视为僵尸锁覆盖
7. 运行流水：`.ingest-history.log` append-only，每次一行 JSON（日期 / 模式 / 耗时 / 状态 / commit hash）

## 6. 数据源模型

原则：散乱工作区不靠接入所有设备解决，靠「汇流口优先 + 源可失败 + brain-dump 兜底」。

### 6.1 五类收集器

| 层 | 类型 | 成本 | 说明 |
|---|---|---|---|
| 1 | brain-dump | 零配置 | 触发消息即最后的万能收集器，不用声明 |
| 2 | 托管平台（github / gitlab） | 一次配置 | gh / glab CLI 扫「今天我名下所有仓的 push」，设备维度收敛成平台维度；auth 失效降级为只扫本地并报一行 |
| 3 | local-git 多 root | 便宜 | config 声明搜索根（多硬盘 = 多 root），有限深度自动发现 `.git`；未挂载即记一句跳过；排除 `refs/stash` 伪 commit |
| 4 | remote-ssh | 贵，按需 | 仅给「工作不经过平台」的机器；参数化 `scan.sh` 本地远程同一脚本（`ssh host 'bash -s' < scan.sh`）；连通性文档推荐 Tailscale |
| 5 | vault 内部状态 | 内置 | memory 目录 mtime + wiki / diaries 改动感知（ingest 自身状态源，不属于外部四层） |

IM 协调源（type: im，经连接器接入，见 §6.3）与上表并列。

### 6.2 config 草案

```yaml
schema_version: 1
timezone: Asia/Shanghai          # init 时询问
day_boundary: "07:00"            # 日期分割线，可配（00:00 至分割线归前一天）
language: zh                     # locale 模板 / 写作规范 / 标点门按此切换（v0.1: zh / en）
identities: [me@personal.com, me@company.com]   # 多署名过滤，init 从 git config 预填
sources:
  - {type: github, account: xxx, assume: active}
  - {type: local-git, roots: [~/projects, /Volumes/T7/work], exclude: ["**/tmp-*"], assume: active}
  - {type: remote-ssh, host: workbox, assume: active, on_unreachable: note}
  - {type: im, provider: feishu, via: lark-cli, on_unreachable: note, record_others: false}
  # - {type: local-dir, path: ~/writing/novel, track: mtime}   # 非 git 项目须显式声明（§6.4）
projects:
  default_level: detail            # 已定级项目的默认记录级别（§6.4 四级）
  on_new_project: presence         # 新发现项目的初始级别（安全默认，§6.4）
  overrides:
    - {match: "~/employer/**", level: summary}
modules:
  life_section: true             # 日记「生活」段可选
diary_title_template: "# 工作日记：{year}年{month}月{day}日（{weekday}）"   # 属 locale 模板，可自定义
```

`worklog-init` 交互问的不是「你的项目在哪」，是「**你的工作都发生在哪**」，逐个生成 source；日记项目段标注来源（扫描 vs 口述）。

### 6.3 IM 连接器接口

IM 是最因人而异的数据源，必须连接器化。每个连接器实现四件事：

1. **认证自检**：可用则通过，不可用（未装 / 未授权 / 企业管理员限制）则在 config 禁用该源并明确告知，ingest 永不因 IM 失败挂起
2. **拉取当日与我相关的消息**：按 §9.4 最小记录默认
3. **输出统一 digest 格式**：供 ingest 的协调段模板消费（模板子层由 config 声明，不硬编码角色 / 群结构）
4. **降级行为**：token 过期 / 网络失败记一句 + 晨起报告给出重新认证命令

v0.1 内置 **feishu** 参考实现（官方 `@larksuite/cli`，`feishu-setup` skill 负责安装认证与坑文档：Keychain 降级、`bash -lc` 加载 node、token 约周级过期）。slack / 企业微信 / Teams 等按接口扩展，列入 roadmap 或社区贡献。不配任何 IM 源也完全可用。

### 6.4 项目发现与记录同意

设计前提：**没有人能完整枚举一台机器上有哪些私有项目，维护者不能、用户自己在 init 那一刻也未必能**。所以发现必须全自动，但「发现」不等于「记录」，两者之间隔一道用户同意：

- **四级记录级别**（per 项目）：`detail`（详记：commit 内容、决策、建 wiki 项目页）/ `summary`（一句概要 + 计数，不建项目页）/ `presence`（只记存在与 commit 数，不读内容）/ `exclude`（完全不记，日记不出现）
- **init 扫描预览**：初始化跑一遍全量发现，把找到的项目清单摆给用户逐个定级；这一步同时帮用户看清「原来这些也会被扫到」，是同意机制的第一道闸
- **新项目安全默认**：日常 ingest 自动发现的新项目，初始级别 = `presence`（当晚只记「新发现项目 X：N commits，待定级」，不读内容），晨起报告列「待定级」清单，用户一句话升降级；接受全自动详记的用户可 config `on_new_project: detail`
- **项目侧否决权**：项目根放 `.worklogignore` 标记文件 = 永久 `exclude`，跟随项目移动、优先级高于 config
- **非 git 项目**：自动发现只认 `.git`（其余目录噪音太大）；无 git 的项目（文档 / 设计 / 写作类）经 config `local-dir` 显式声明，按 mtime 追踪（v0.1 仅 presence 级，详记后置）
- **项目身份**：slug = 目录名；跨 root 同名冲突自动加 root 别名前缀；嵌套子仓默认归并父项目页，config 可拆分

## 7. Skill 需求要点

| skill | 关键需求 |
|---|---|
| worklog-init | 环境预检（git user.name/email、remote 与 push 鉴权 dry-run、gh auth、uv、OS 检测且 Windows 原生直接报错退出）；仓库 visibility 检测（非 private 红色警告并暂停）；config 交互生成（语言 / 时区 / 分割线 / 身份 / 数据源）；扫描预览与项目定级（§6.4，同意机制第一道闸）；locale 骨架实例化；三件套全局安装（§4.2，vault 内 cp，无网络拉取）；`docs/dev/` 一键移除选项；冷启动（§10）；完成后生成 GETTING_STARTED.md（.gitignore 内） |
| worklog-ingest | 见 §8 |
| worklog-import | `uvx markitdown` 转换 docx / PDF / pptx 等入 `inbox/`；图片 LLM 描述默认关；ingest 不自动扫 inbox（防耗时爆炸），只引用当天新增条目 |
| feishu-setup | §6.3 连接器接口的首个参考实现 |
| worklog-query | 「查 X」跨日记 + wiki 检索行为显式化 |
| worklog-lint | 通用项：断链、frontmatter 完整、凭证扫描（含截断 token 前缀）；中文 locale 可选项：标点门（punctuation_check.py 随包，`language: zh` 才加载）；个人演化项不进 kit |
| worklog-update | 只 rsync `.claude/skills/` 白名单路径（含三件套快照），其余 hard deny（§12） |

## 8. worklog-ingest 重写规格（核心工程）

审计结论：私有版 SKILL.md 近 1000 行中维护者专属内容超 40%、散布 20 余处，**重写而非删改**。目标体积 ≤500 行（同时缓解弱模型指令遵循与单晚 token 消耗）。

**保留骨架（方法论本体，原样继承）**：
- 5 步流程（自扫 → 解析 → 一行回执 → 自主跑 → 晨起报告）与时间窗口公式 [D day_boundary, D+1 day_boundary)
- 三模式防覆盖（新增 / 补充 / 更新 + 触发语与文件实测共同决定 + auto-fallback）
- 无人值守铁律 + 默认值表机制（表内容由 config 生成）
- judgment 提炼、四元素、(B) 类自维护工作记录（四类简化为两类）
- index 头部封顶、项目页 frontmatter 刷新、TODO 盘点
- commit + push 闭环（push 前 visibility 检测，见 §9.2）

**删除（维护者专属，不迁移）**：身份锁死声明、具名远程源整块逻辑、IM 群坐标与角色专属子层、求职模块、私有 memory 引用（20+ 处）、公开镜像脱敏 SOP 节、个人项目特例路由。

**config 化**：扫描列表与项目根假设 → sources；机器名默认值 → 每 source 的 assume；时区与分割线 → config；`WORKLOG` 路径锚点 → `git rev-parse --show-toplevel` 动态推导；日记标题模板、生活段开关、语言。

**降级矩阵（每源必答两问：连不上怎么办 / 鉴权失效怎么办）**：全部走「记一句 + 继续 + 晨起报告列清单」，IM 连接器 token 过期额外提示重新认证命令。

**git 安全三件**：开跑先 `git pull --ff-only`（失败不 rebase 不 merge，降级记录）；`.ingest.lock` 并发锁；Edit 锚点找不到时 fallback 为 append 文件尾 + status 记一行（兼容用户已演化结构，绝不报错中断）。

## 9. 安全与隐私（出厂默认）

1. **权限**：模板随附 `.claude/settings.json`，allow 清单精确列出 ingest 用到的命令模式（git / ssh / python3 / find / date 等），不开 bypassPermissions；README troubleshooting 写明首跑弹权限的处理
2. **公开仓双检**：init 时 + 每晚 push 前 `gh api` 查 visibility，发现 public 立即中断 push 并红色警告（use-as-template 误选 public、日后手动改公开都在此拦截）
3. **凭证隔离**：config 两层（base 入 git 零凭证 / local 不入 git）；.gitignore 预置 `.ingest-status.md`、`.ingest.lock`、`worklog.config.local.yaml`、`.obsidian/workspace*`、`.env*`、`*.key`、`*.pem`、`id_rsa*`、`credentials*`、`GETTING_STARTED.md`、`.DS_Store`
4. **IM 最小记录**（所有连接器统一）：默认只记用户本人发的消息，记录他人需显式 `record_others: true` 且 README「IM 数据使用须知」写明合规责任（被记录同事、雇主信息安全政策、私仓仍在第三方服务器）；不臆断对方确认、清单类逐字照录等纪律进 skill 本体
5. **数据所有权**：diaries / wiki 是标准 markdown；提供 worklog-export（去 Tasks 语法 + wikilink 转普通链接）作退出通道
6. **零遥测 + 脱敏诊断**：kit 不回传任何数据，维护者永远看不到用户的项目与日记；报 issue 用脱敏诊断输出（环境版本 + 各数据源匿名化状态，项目名与路径经占位符化），issue 模板只收这份输出，杜绝用户为求助而贴出私有项目信息

## 10. 冷启动与首周体验

- **日记侧**：init 回填最近 **3 天简版**日记（概览 + 时间线 + commit 列表，不跑完整 judgment，标注「自动回填、信息有限」）；仅回填 init 预览中定级为 detail / summary 的项目；天数可选。否决项：14 天全量回填（数小时 + 数百万 token，首日体验反噬）
- **wiki 侧**：worklog-import 批量转换用户存量文档入 inbox/，第一天打开不是空库
- **首周**：GETTING_STARTED.md 教第一晚 brain-dump 怎么说、次晨如何用「更新日记」订正、说明前三天是磨合期 + 首跑 FAQ

## 11. 可观测性

`.ingest-status.md`（卡点与自救命令，成功时标 last-success）+ `.ingest-history.log`（运行流水）+ Step E 晨起报告（含降级源清单、未附带信息提示）。

## 12. 升级与兼容

- worklog-update 安全边界：只同步 `.claude/skills/` 下白名单文件（kit 自有 skill + 三件套快照统一经此更新），绝不 `git merge` upstream，绝不触碰 diaries / wiki / config
- config `schema_version`：skill 启动断言版本，update 后不匹配则输出需补字段 + 默认值；版本过旧给明确报错不静默异常
- 三件套快照经 `scripts/sync-upstream.sh` 从 personal-skills release tag 单向同步，CI 做 drift 提醒
- update 后自动 dry-run 检测 wiki 结构与新版 skill 预期的兼容性，不兼容输出手动调整清单

## 13. 上游 personal-skills 配套修复（随 kit 一并做）

- stash/check.sh 与 aireadme/check.sh locale 策略统一为 `LC_ALL=C`；description 计数只走 python3 分支；README 声明 bash / python3 前置
- aireadme check.sh 状态表表头兼容中英文；边界粗查补英文关键词；STANDARD.md 加「产出语言跟随项目主语言」指令
- stash 路径推导加实测兜底（先 ls `~/.claude/projects/` 找实际存在目录，推导仅作 fallback）；MEMORY_SPEC 全角冒号降为可选偏好
- pitfalls LIBRARY.md 种子坑标注平台 / bash 版本适用范围，补少量 Linux 常见坑；打 release tag

## 14. 明确不做（v0.1）

- 每台设备装采集 daemon 的 push 模型（v2 可选进阶）
- 缺口自动回补（硬盘插回只记一句滞留 commit，回补走补充模式手动触发）
- homepage 通用化（phase 2 独立立项）
- Codex 双运行时支持（仅 AGENTS.md 指针，Codex 产出靠 git 天然捕获）
- Obsidian 硬依赖（推荐查看器：附最小 `.obsidian/` 配置让 Tasks 插件即装即用）
- Windows 原生支持（WSL 实验性）
- plugin 市场分发（发布后按用户规模再评估）
- feishu 之外的第二个 IM 连接器（接口先行，实现按需求排期或社区贡献）
- aireadme STANDARD.md 全文英文化（上游事项，后置）

## 15. 里程碑

- **M1 模板骨架**：仓根即模板重构（docs/dev/ 隔离）+ 契约文件全套预置（zh / en 双 locale 模板）+ settings.json + 三件套 vendor 快照与 sync 脚本 + worklog-init（预检 / config 生成 / 全局安装 / dev 文档移除）
- **M2 ingest 重写**：§8 全部 + scan.sh 可移植版（BSD / GNU 通用写法：`touch -t` + `find -newer`，不用 `date -v` / `-newermt`；每 root 扫描超时保护）
- **M3 连接器**：github 收集器 + IM 连接器接口定稿 + feishu 参考实现 + worklog-import
- **M4 收尾**：query / lint / update + README 产品叙事（中英双语）+ GETTING_STARTED + CI（shellcheck + punctuation_check pytest + 三件套 drift 提醒）+ 极简 CONTRIBUTING 与 issue 模板
- **M5 pilot 与发布**：两位种子用户试用（一个飞书重度 + 一个纯本机），企业飞书授权实测，按摩擦迭代；公开发布前过对抗式泄漏审计

## 16. 开放问题

- pilot 人选待定
- 发布时机：公开前须过对抗式泄漏审计（含本 PRD 与 git 全历史）
- personal-skills release tag 首版版本号
- 第二个 IM 连接器（slack / 企业微信）的时机与归属（维护者 or 社区）

## 17. 依赖与许可

- lark-cli = 飞书官方 `@larksuite/cli`（npm），文档指引安装，不随包分发
- markitdown = microsoft/markitdown（MIT），经 `uvx` 调用
- gh / glab（按需）、uv、python3、bash 3.2+（scan.sh 兼容目标）
- 三件套快照源自 personal-skills（Apache-2.0，同许可 vendor 合规）
- 本仓 License：Apache-2.0（与 personal-skills 一致）

---

## 修订记录

- **v0.3（2026-07-11）项目发现与记录同意**：确立「发现 ≠ 记录」（§6.4）。没有人能枚举用户机器上的私有项目（维护者不能、用户自己也未必能），故发现全自动、记录须同意：四级记录级别（detail / summary / presence / exclude）+ init 扫描预览定级 + 新项目安全默认 presence + 项目侧 `.worklogignore` 否决权 + 非 git 项目显式声明 + slug 冲突规则；§9 增补零遥测与脱敏诊断。这是维护者「RAG 排除 / 特定项目不进扫描列表 / 无 git 项目特批」等个人实践的产品化。
- **v0.2（2026-07-11）通用化修正**：产品定位从「给朋友用」升级为「任何人拿来即用」。四处修正：① 定位与目标用户改为能力定义（硬前提只有 Claude Code + git），朋友画像降为种子用户；② 飞书从一等必选模块降为 IM 连接器接口（§6.3）的首个参考实现，不配 IM 也完全可用；③ 三件套从「init 运行时在线拉取」反转为「vendor 固定版本快照随模板分发」（通用产品必须自包含）；④ 确立「仓根即模板」架构，开发文档隔离 `docs/dev/`，根 CLAUDE.md 为面向用户的产品件；另：契约骨架增加 zh / en 双 locale 模板。
- **v0.1（2026-07-11）立项定稿**：四轮孵化讨论 + 112 条设计审计收敛。
