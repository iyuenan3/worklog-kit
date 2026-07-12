# CHANGELOG（append-only）

> 倒序版本块，每块 = 版本 + 日期 + `Added/Changed/Fixed/Removed`，格式参考 [Keep a Changelog](https://keepachangelog.com/)。**单一版本流**：以下先是 worklog-kit 的发布史（你的 vault 诞生自哪个版本），init 之后 vault 自己的里程碑（初始化、schema 大改、数据源增减、skill 升级）继续在顶部叠加。

## Unreleased · vault 记忆维护（体检 + 修复，2026-07-12）

摄入时编译架构的盲区补批处理维护工序（PRD §18；设计参考 InquisiMind/digital-life 的维护工序思想）：

### Added
- `lint.py --health` 健康节：五项零 LLM 指标（状态漂移 / 孤儿页 / 实体分裂候选 / 膨胀 / TODO 年龄），阈值读 config `maintenance:` 段（全可选、内置默认值，schema_version 不升版保老 vault 零动作兼容）；退出码 0 健康 / 2 有待维护项；`--today` 供测试固定时钟；alias 存根（frontmatter `alias_of:`）与 `wiki/archive/` 不参与体检、`#todo/stale` 已分诊任务不重复报（保证体检可归零）
- ingest D.4 体检提醒行：超阈值才在当天日记末尾追加一行指引，健康时零痕迹；同日补充已有行则原地更新数字、清零改写不删行（日记只追加）
- `worklog-maintain` skill（本功能唯一新增，双 locale 路由）：现场体检 → 按腐坏类型分批修复每类一 commit → 全门验收出小结；授权跟触发方式走（交互 = 明示授权直接修，无人值守只报告）；三红线（diaries 永不触碰 / wiki 只合并归档重链 / TODO 僵尸只标记）
- 文档三小件：`docs/maintenance.md`（schedule 月度报告模式配方 + `~/.claude` memory 瘦身手工配方）、`docs/dev/deep-review.md`（深度 review 方法论占位，明确不产品化）
- tests/test_health.py 12 例；fixture vault E2E：五类腐坏注入 6 项全检出 → 5 类修复（6 → 1 → 0）→ 提醒行三路径 → 四门全绿

## Unreleased · 第五轮 review 修复（workflow 对抗审查，2026-07-12）

6 维 workflow 对抗 review（22 条原始 → 去重 16 条 → 每条 3 视角验证），11 条确认全处置、5 条驳倒不修（多 vault 串查 / 插件预启用信任 / OS 守卫措辞 / 触发词微差 / 树图省略均有既定依据）：

### Fixed
- **P0 收窄为最小权限**：settings.json `Bash(obsidian:*)` 通配符（放行含 eval / delete permanent / plugin:install 在内全部子命令且可跨 vault）改为查询型命令逐条白名单（search / read / files / tags / tag / links / tasks / vault）；增量风险本就有限（清单原有 bash:*），但执行层与 skill「只用查询型命令」口径应一致
- **P1**：README 双语 inbox 行「当晚消化」改「当晚日记引用；深度消化说一声」（对齐 ingest / import / PRD 三处既有口径）；.gitignore `.obsidian/workspace*` 改 `.obsidian/*` + 两个模板文件白名单否定（防 Obsidian 自动生成配置弄脏 git status、被 ingest 残留规则误提交）
- **P2**：README 双语 Obsidian 条目修正（CLI 仅关键词类检索走、删与「以文件为准」矛盾的「更准」、双链图谱归还 Obsidian 本体、en 补齐修饰语）；visibility 检测两处补「装有 gh」前提（原无条件语气，未装 gh 实际静默降级）；PRD（头部 / §15 / §16 / 修订记录 v0.5）与 DEV.md 红线同步「2026-07-12 已提前公开」现实，即时公开 + 禁改已 push 历史入红线；根 CLAUDE.md 双 locale 路由表 lint 行补齐第四轮口径（日期门 zh / en 都跑）；「接口文档见上一节」改直给路径
- **P3**：en 直译腔两处（knowledge settles → accumulates；design intent, not off-road → all by design, not a deviation）

## Unreleased · Obsidian 可选集成（2026-07-12）

「复用 Obsidian CLI」提议的评估落地：唯一真重叠处（query 的检索原语）吃满，无人值守铁律与通用性红线不动，Obsidian 保持非硬前提（PRD §14 否决项不变）：

### Added
- worklog-query 新增「Obsidian CLI 优先」检索通道：探测（`command -v` + 只读命令试跑）→ macOS 后台拉起（`open -ga`，不抢焦点，回答里提一句）→ 静默回退 rg / grep；只用查询型命令，绝不用会弹前台的 open / daily
- 模板补齐最小 `.obsidian/` 配置（app.json + community-plugins.json 预启用 Tasks）：装上 Tasks 插件即得 TODO 聚合视图，兑现 PRD §14「推荐查看器附最小配置」的既有承诺
- settings.json 补 `Bash(obsidian:*)` 与 `Bash(open -ga Obsidian)` 两条 allow

### Changed
- README 双语 Obsidian 推荐语加重为独立条目（强烈推荐但保持可选，说明 CLI 加速与 Tasks 即装即用）；PRD §7 query 行同步检索通道口径

## Unreleased · README 可读性重构（2026-07-12）

### Changed
- README 双语整体重构：「它做什么」改为触发语表格（产品交互面一目了然）；快速开始收敛为 3 步 + fork 警示引用块；隐私独立成节；「长成你的样子」升格为重点章节（三层固定 / 生长对照表 + 三个对 Claude 说的实例 + 三条安全轨道 + 收束句）；状态段刷新为「模板已公开，种子用户试用（M5）进行中」

## Unreleased · 新用户上手与自开发口径（2026-07-12）

翻 public + 开 template 后，把口头嘱咐的上手要点固化进产品件：

### Added
- README 双语快速开始第一步强化：Use this template 时 **Visibility 选 Private、不要 fork**（公开仓的 fork 无法转私有），并说明 init 与每晚 push 的 visibility 检测是兜底不是替代
- README 双语新增「接入 IM（可选）」段：feishu-setup 向导入口、默认只记本人消息、企业受限优雅跳过、接口开放可扩 Slack 等（README 原先只在依赖清单提了一嘴飞书，没有配置入口）
- README 双语新增「长成你的样子」段，根 CLAUDE.md 与 en locale 模板「维护」段扩为「维护与自开发」：明确 vault 支持用户与其 Claude 持续自开发（红线之外随用随长；自建 skill 放新目录，worklog-update 永不触碰本地独有 skill，改 kit 自带 skill 升级时逐个确认）

## Unreleased · 第四轮 review 修复（重构回归 + 实排演，2026-07-12）

6 视角（3 实跑重演 + 3 深读），12 条原始收敛为 5 条确认全处置；init / ingest / update 实排演零功能性破坏：

### Fixed
- **P1**：worklog-update 内部矛盾：hard deny 说「两层 config 一律不碰」而 Step 5 让自动追加顶层键，执行者无法同时服从；按 PRD §12 原意收敛为「一律只展示不代写，用户明确授权才动」
- **P2**：PRD 树图注「CONTRIBUTING.md 在仓根」漏改（仓根收缩时遗留）；PRD §6.1 vault 内部源残留私有版「memory 目录」描述（改为与 ingest SKILL 一致的 git log + wiki / inbox 感知）；PRD §7 与 lint SKILL description 仍写「日期门 zh 才加载」（第三轮已改为 zh / en 都跑，两处口径补齐）；ingest Step A im 行残留「跑 feishu-setup 补全」硬编码（错误表第一轮已泛化、此处漏网）

### Added
- 降级路径测试三例（补「每个数据源都可失败」承诺的测试空白）：scan / discover 对未挂载 root 的 SKIP_UNMOUNTED + exit 0、github-scan 无 gh 时 exit 4

## Unreleased · CHANGELOG 合并进 AIREADME（2026-07-12）

### Changed
- 根 `CHANGELOG.md` 删除，发布史并入本文件：kit 发布史与 vault schema 演进合为单一版本流（无需维护两份；worklog-update 的「这次更新带来什么」摘录与发布 tag SOP 改指本文件）

## Unreleased · AGENTS.md 移除（2026-07-12）

### Removed
- 根 `AGENTS.md` 与 en locale 模板对应件：产品硬前提是 Claude Code，vault 约定只面向 CLAUDE.md；Codex 等其它工具的产出靠 git 天然捕获，不再保留指针文件（维护者决定，PRD §14 已同步）

## Unreleased · 仓根收缩（2026-07-11）

根目录只留 vault 本体与 GitHub 惯例件，上游仓专属 / 仅 init 时使用的资产归位：

### Changed
- `templates/locale/` 迁入 `.claude/skills/worklog-init/templates/locale/`：locale 模板本是 init 的实例化资源，与 GETTING_STARTED 模板同居；顺带获得 worklog-update 的同步覆盖（原先根级 templates/ 不在升级白名单内）
- `CONTRIBUTING.md` 迁入 `.github/`（GitHub 认可位置，PR 界面照常展示）：与 CI、issue 模板同组为「上游仓事务」，init 的开发基建移除选项可整体带走
- `worklog.config.local.yaml.example` 删除，内容折叠为两份 config 模板的尾部注释（敏感层说明与示例就近可见，少一个根级文件）

## Unreleased · 第三轮 review 修复（忠实度实跑 + 合规 + 威胁建模 + token 经济，2026-07-11）

fixture vault 实跑 ingest 全流程 + 双审计员对照 ground truth，14 条确认全处置。核心发现：执行者自评「无编造」，独立幻觉审计员实锤 6 处编造的决策理由入日记并沉淀进 wiki 决策日志（P0）。

### Fixed
- **P0 幻觉逃生舱**：ingest「有决策必写 why」补硬约束：why 只能转述素材原文，素材未述写「理由素材未述」+ ⚠️，禁止推测补全（D.1 judgment 与 D.2 项目页决策日志两处）
- **P1**：时间线禁编钟点（brain-dump 只说「下午」就写「下午」，估算排序必标 ⚠️ 与推断依据）；exclude 级从「日记不出现」收紧为「全部 git 追踪产物零出现」（log.md 原会写出被排除项目名，泄漏用户要藏的项目）；summary / presence 级的时间线行为显式化（聚合一行，不逐条展开）；init 定级前必须先展示四级数据维度表 + 雇主合规提醒（不看表选 detail 等于不知情同意）；init Step 6 全局安装补供应链信任模型（首装也要先看内容再 cp）
- **P2 执行猜测点 ×6**（executor_notes 转化）：overrides glob 匹配语义、`{weekday}` 解析规则（config 双语注释 + D.1）、Co-Authored-By 模型名推导、index「最后更新」行格式、`init:` 脚手架 commit 不算工作线、`git_commits` 计数口径；README 双语补「一晚花多少额度」与限流中断预期

### Added
- 日期门支持 en 写法（frontmatter `day: Saturday` + 「YYYY-MM-DD (Saturday)」，非星期括号词跳过）；lint 写作门口径改为「标点门仅 zh、日期门 zh / en 都跑」；tests 补 en 三例
- ingest 错误表补「上次运行崩溃残留」行（残留改动先单独 commit 再开跑）
- PRD §16 开放问题补「skill 指令面 zh 单语，是否翻译待 pilot 反馈」

## Unreleased · 第二轮 review 修复（换视角，2026-07-11）

第二轮 8 个全新视角（执行歧义 / 恶意输入 / 时间并发 / 长期规模 / 越轨用户 / 发布形态 / 回归 / 反向契约），13 条确认 + 3 条存疑全处置：

### Fixed
- **P1**：remote-ssh 源补 `roots` 字段（config 双语模板 + PRD + init 必追问 + ingest 缺失降级，原 schema 无此键、无人值守时只能瞎猜路径）；feishu fetch.sh 命中单页上限（50 条）输出 NOTE（实证 lark-cli 的 `+chat-messages-list` 无自动翻页，活跃群会静默丢消息；接口契约同步进 connectors/README）；移除 config 哑键 `sources[].exclude`（全无消费者，`.worklogignore` 与 overrides `level: exclude` 已覆盖需求，PRD §14 记否决理由）
- **P2**：scan.sh 与 discover.sh 改 `-print0` 读取并跳过含换行路径（防幻影条目污染行协议）；lint 对非 `YYYY-MM-DD.md` 命名的日记杂件（同步冲突副本）降为 advisory 不再卡红；凭证扫描支持行内 `lint:ignore` 豁免标记；日期门 `--all` 改递归遍历 diaries 子目录（与 lint 口径一致）；DEV.md 定发布 tag SOP（semver `vX.Y.Z` + CHANGELOG 对应）；README 双语 GitLab 标注「计划中」并补依赖版本下限；ingest 补 BRANCH 信号消费规则、local-dir 行去掉误导的 scan.sh 用法、Step A 澄清 vault 内部源不属 config、D.2 锚点名跨 locale 对照（en vault 不再每晚走 append 兜底）；PRD 树图补省略说明；en locale CLAUDE.md 补 dev 指针行（init Step 7 清理目标对齐）

### Added
- CI 矩阵加 macos-latest（BSD find / sort / grep 与 bash 3.2 是产品声明，只测 GNU 等于没测可移植性）
- lint 新增 wiki/index.md 增长阈值 advisory（800 行提示按年归档）；tests 补冲突副本与 lint:ignore 两例回归

## Unreleased · 全仓 review 修复（M5 前，2026-07-11）

18 条确认发现（8 维审计 + 逐条对抗验证）全部修复：

### Fixed
- **P1**：`scan.sh` 与 `discover.sh` 的 find 加 `-H`（root 为符号链接时静默零输出、exit 0）；feishu `fetch.sh` 捕获解析器退出码（崩溃时输出 NOTE + 非零退出，原为静默丢整个会话）；标点门剥离图片语法 `![alt](url)`（原残留孤儿 `!` 误报）；`lint.py` 日记 frontmatter 改逐行读到闭合 `---`（原 `read(400)` 截断长 frontmatter 误报缺失）；worklog-init 流程标题改 9 步（原写「7 步」会让执行者漏跑 Step 8 与 9）；init Step 7 移除 `docs/dev/` 后同步清理 README 双语与 CONTRIBUTING 的引用（原留三处死链）
- **P2**：ingest SKILL 的 im 降级列去 feishu 硬编码（自救命令改为转发连接器 check.sh 自带输出）；错误表「fetch exit 2」误导口径改为「Step A 前置检查拦截」；`date_weekday_check.py` 文件读取失败改退出码 3（与标点门契约对齐，原误计入不一致）；feishu `check.sh` 补 python3 探测（原假绿）；settings.json 摘除飞书专属权限三条（feishu-setup 启用时追加，产品级清单保持连接器无关）；`.gitignore` 补 `export/`；config 双语模板与 PRD 补 `github_slug` 文档；PRD 修 §4.1 树图（CONTRIBUTING 位置 + 补 worklog-export）、§7 补日期门、§8 四模式、§9.3 gitignore 清单、头部状态刷新至 v0.4；本文件三个里程碑标题补齐日期

### Added
- `templates/locale/en/wiki/projects/.gitkeep`：en locale 模板成套（原缺 projects/ 目录）
- `tests/test_scan_discover.py`：scan.sh 与 discover.sh 的 fixture 级行为测试（含符号链接根回归用例）
- worklog-update 与 PRD §12 补供应链信任模型说明（tag 锁定 + 差异盘点即审计点，v0.1 无签名校验）

## M4 收尾（2026-07-11）

### Added
- `worklog-lint`：lint.py 机械项（契约锚点 / 凭证扫描 / 断链剥代码段 / frontmatter / log 轮转阈值，🔴🟡 退出码约定）+ zh 写作门编排（复用标点门与日期门，缺脚本优雅跳过）
- `worklog-query`（只读、按意图分流、答案带出处）/ `worklog-update`（镜像同步 .claude/skills 白名单 + tag 锁定 + 顶层键追加式 schema 迁移 + 锚点兼容 dry-run + `upstream_repo` 支持 fork）/ `worklog-export`（退出通道：wikilink 去方言 + Tasks 查询块与行尾元数据清理）
- README 中英双语（README.en.md）+ 状态段刷新至 M1-M4 完成
- CI（bash -n + shellcheck errors + settings JSON + aireadme check + vault 自检 + pytest）+ tests/test_gates.py（三脚本 CLI 级 10 例）+ 极简 CONTRIBUTING + 双语 bug issue 模板

### Removed
- 「三件套 drift 提醒 CI」不再需要：v0.4 canonical 迁入本仓后无跨仓同步，该项随之废止

## M3 连接器（2026-07-11）

### Added
- `github-scan.sh` GitHub 收集器：发现（user/repos 按 pushed 窗口）+ 精扫（逐仓 commits API，author 按账号维度覆盖全部关联 email）两段式；与本地扫描按 commit hash 跨源去重、本地优先；已在真实账号实测
- IM 连接器接口 v1（`connectors/README.md`）：check.sh 三态退出码 + fetch.sh digest 行协议 + 隐私契约（record_others 在采集层执行）+ 降级契约（内部自带超时、绝不交互）
- feishu 参考实现（`connectors/feishu/`，基于官方 `@larksuite/cli` 实测命令面）：warning 行过滤、JSON 字符串正文二次解析、perl alarm 可移植超时、结构未识别时 NOTE 降级
- `feishu-setup` skill：安装 / 应用凭证 / Device Flow 授权 / macOS keychain-downgrade 权衡 / 会话发现与挑选 / 企业受限优雅禁用 / 自检试拉
- `worklog-import` skill：markitdown 单文件与批量摄入 `inbox/`（provenance frontmatter + 扫描版 PDF 标注 + 超量先确认）；worklog-init 补 Step 9 存量迁移
- ingest 接入 github / im 两源（降级矩阵扩展）+ 跨源去重规则

## M2 ingest 通用版（2026-07-11）

### Added
- `worklog-ingest` skill 通用重写（config 驱动、零硬编码、约 190 行）：四模式（新增 / 补充 / 更新 / 回填）+ 无人值守铁律 + config 生成的默认值表 + 分级记录过滤（detail / summary / presence / exclude + 新项目待定级）+ 降级矩阵 + git 安全三件（ff-only 拉取 / `.ingest.lock` / 锚点 append 兜底）+ visibility 检测 + `.ingest-history.log` 观测
- `scan.sh` 可移植扫描器：自足单文件（`ssh 'bash -s'` 直发远端）、`--since/--until` 直传 git 零 shell 日期运算、identities 多作者过滤、`--branches --tags` 排除 stash 伪 commit、DIRTY 计数、mtime 兜底（`touch -t` + `find -newer`）、可选 GNU timeout 保护
- 校验脚本随包：`punctuation_check.py`（zh 标点门）+ `date_weekday_check.py`（日期门，星期映射禁心算）
- worklog-init 接入 Step 8 冷启动回填（默认 3 天简版，经 ingest 回填模式）

## M1 模板骨架（2026-07-11）

### Added
- 立项与 PRD（v0.4，`docs/dev/PRD.md`），产品叙事 README
- 契约骨架：`diaries/` `inbox/` + wiki 四件（index / log / todos / projects/，zh 默认 + en locale 模板）+ 双层 config（base 入 git / local 排除）+ `.gitignore` 全清单 + `.claude/settings.json` 权限 allow 清单
- `worklog-init` skill：环境预检 / config 交互生成 / 扫描预览与项目定级 / 三件套全局安装 / dev 文档移除
- 三件套（aireadme v0.2.1 / stash / pitfalls）与 project-lifecycle 方法论（`docs/methodology.md`）自 [iyuenan3/personal-skills](https://github.com/iyuenan3/personal-skills) 迁入（2026-07-11，provenance = 其 main 当日状态；personal-skills 侧指针在 kit 公开时同步落地）

### Changed
- 三件套随迁修缮：stash/check.sh locale 统一 `LC_ALL=C`、计数只走 python3；aireadme/check.sh 表头与边界粗查兼容英文；STANDARD 增「产出语言跟随项目」；stash 路径推导加实测兜底、索引分隔符降为可选偏好；pitfalls 种子坑标注平台 / bash 版本适用范围，新增「非交互 SSH 不加载 rc」条
- 四视角对抗验证（38 条发现）修复：en locale 补齐全套产品件（CLAUDE / AGENTS / AIREADME 12 件 / config，AGENTS 后于 2026-07-12 移除）；settings.json 补 init 全部所需命令；stash 英文 How-to-apply 校验补 bold 口径；discover.sh 发现深度默认 4（修 off-by-one）并 prune 隐藏目录与 node_modules；worklog-init 修 GETTING_STARTED 路径 / WSL 辨识 / gh auth 预检 / 无 remote 分支 / overrides 格式规范；skill README 安装后断链改绝对 URL；config 增 `index_recent_days`
