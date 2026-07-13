# CHANGELOG（append-only）

> 倒序版本块，每块 = 版本 + 日期 + `Added/Changed/Fixed/Removed`，格式参考 [Keep a Changelog](https://keepachangelog.com/)。**单一版本流**：以下先是 worklog-kit 的发布史（你的 vault 诞生自哪个版本），init 之后 vault 自己的里程碑（初始化、schema 大改、数据源增减、skill 升级）继续在顶部叠加。

## Unreleased · 多 git 仓与非 git 项目实态修正（PRD v0.7，2026-07-13）

源于「一个项目下多个 git 仓 / 非 git 项目怎么处理」两问的端到端审计（4 facet fixture 实跑 + 每条发现 3 视角对抗验证，21 条原始 → 12 确认全处置、9 驳倒）：

### Fixed
- **P1**：local-dir 活动判定无窗口上界（SKILL 内联配方只造「窗口起」参照，目录在目标日之后动过就把每个历史日记成有活动，「补充昨天 / 回填 N 天」必错账）：下沉为 `localdir-scan.sh`，双参照定窗 `find -newer 起 ! -newer 止`
- **P2**：submodule 是发现与扫描双盲区（`.git` 为 gitdir 指针文件，`-type d` 永不匹配，submodule 内 commit 主仓 log 不含、自身又不被发现，整天工作从日记消失）：find 增配 `-type f -name .git`，指针分类后按独立仓照常扫，fixture 实测内部 commit 完整捕获；worktree 检出出 `WORKTREE_SKIP` 信号不独立扫（共享 refs 双扫会重复计 commit），bare 仓明确为不支持边界（PRD §14 + README 双语 Troubleshooting）
- **P2**：local-dir 零噪音防护（.DS_Store / node_modules / 隐藏目录 / 无限深度全算活动，Finder 浏览一次即假活动）：隐藏目录 / node_modules 与 scan.sh / discover.sh 同口径 prune + 深度默认 4（config `depth:` 键可调）+ 隐藏文件不算活动；scan.sh 自身 MTIME 兜底同步修嵌套仓与隐藏文件串扰（嵌套仓 prune 为 scan.sh 特有：子仓已独立成段，活动各归各）
- **P2**：PRD §6.4 两句失实承诺处置：「嵌套子仓默认归并父项目页」零实现且与 scan 行协议相反 → 改口认账「嵌套与并列多仓一律各自独立成项」（多仓归组列 §16 开放问题）；「跨 root 同名加 root 别名前缀」零实现 → 落地为 ingest slug 消歧规则（同名全部加父目录名前缀 + 绝不两项目共写一页 + github 归并 basename 判据失效时不自动归并、晨报提示补 `github_slug`）
- **P3**：嵌套子仓使干净父仓 DIRTY 恒 ≥1（`?? sub/` 结构幻影，presence 级父仓永远到不了「无信号可省略」）：DIRTY 统计跳过「内容全为嵌套仓」的未追踪目录，真实未追踪文件照常计；config 字面 `~` 路径在 local-dir 曾被误报「路径不存在」：脚本兜底展开（与 scan.sh 同）；参照文件明确进 TMPDIR（防落 vault 弄脏 git status）

### Added
- `localdir-scan.sh`（local-dir 源首个脚本承载）+ `tests/test_localdir_scan.py`（窗口上下界 / 噪音 / 深度 / 缺路径 / `~` 展开 / 非法参数 / 多 path / TMPDIR 故障区分）
- tests/test_scan_discover.py 新增：嵌套幻影过滤与真 untracked 保留、submodule E2E（真 `submodule add`）、worktree 跳过不重复计、separate-git-dir、MTIME 串扰回归等
- ingest SKILL「项目身份（slug）」与「WORKTREE_SKIP 信号消费」两节；init Step 5 清单口径（git 形态边界如实告知）

### Fixed（本轮 6 维对抗验证轮：96 agent、30 条原始收敛 23 条确认全处置、7 条驳倒）
- **P1**：ingest 的 local-dir 调用模板缺 TZ 约束（Claude Code 沙箱注入太平洋时区，touch -t 按进程时区解释，照字面执行活动整体平移约 15 小时记错日）：local-dir 与 local-git 调用行焊死 `export TZ=<config.timezone> &&` 前缀，脚本头注补警示
- **P2**：worktree 判据 `gitdir:*/worktrees/*` 路径子串匹配误伤独立对象库（`--separate-git-dir` 到名含 worktrees 的目录、worktree 内 submodule，commit 静默丢失）：改语义判定 git-dir ≠ git-common-dir ⇔ linked worktree，六种 .git 形态 fixture 实测零误判
- **P2**：DIRTY 嵌套仓幻影过滤对空格 / 中文目录名失效（porcelain 引号转义致模式不匹配，原「保守分支」实为不可达死代码）：改 `--porcelain -z` 解析（rename / copy 双段记录多吞一段防双计）；幻影判据从「无普通文件」放宽为「无任何非目录条目」（symlink 是 git 一等追踪对象，只含 symlink 的未追踪目录算真实内容）
- **P2**：`WORKTREE_SKIP` 信号只有 worktree 路径，SKILL 承诺的「判断主仓是否有对应 REPO 块」不可执行（remote-ssh 源彻底走不通）：信号改为 `WORKTREE_SKIP <worktree> -> <主仓路径>`（自 git-common-dir 推导），消费规则改纯机械比对
- **P2**：worktree / submodule 绕过 `.worklogignore` 否决权（exclude 项目的 worktree 路径泄进晨报；exclude 树下 submodule 以全量 commit 浮出）：否决权升级为子树否决（`is_ignored` 祖先逐级检查，两脚本同一纪律），主仓被否决的 worktree 整行静默
- **P2**：slug 消歧「同晚」瞬时判定无持久化，同一项目跨夜在裸名与消歧名间摇摆必出实体分裂双页：消歧结果写进项目页 frontmatter 可选 `path:` 锚点（CONVENTIONS 双 locale 同步），定 slug 改为「查锚点 → 无冲突 basename → 消歧」三步；上溯格式写死叠加式（`work-x-app`，非替换式）
- **P2**：local-dir 深度默认 4 在生产调用面零暴露（深目录活动静默漏记且无调整通道）：config 条目加可选 `depth:` 键（zh / en 模板同步）、SKILL 调用行透传 `--depth`、init 问答提示深目录配 depth，能力边界（4 层 / 隐藏文件不算活动）写进 SKILL；**存量用户注意**：按 客户/年/项目 深层组织的 local-dir 目录升级后需配 depth，否则深层活动记为无
- **P3**：三脚本 `--depth` / `WORKLOG_DISCOVER_DEPTH` 非数字时静默零输出（与「真没活动」不可区分）：前置校验 exit 2；localdir-scan 区分「TMPDIR 不可写」与「时间格式错」两种故障报错；scan.sh 的 `--touch-since` 原在生产调用链无人传参（MTIME_ACTIVE 永不触发却被 presence 判据消费）：接进 ingest 当天模式（回填与 remote-ssh 不传，注明理由）；scan.sh 噪音注释「与 localdir 同口径」收窄为实际共享的部分

## Unreleased · 第六轮 review 修复（全仓深度审查，2026-07-12）

8 维全仓深审（全链路排演 / 脚本实跑 / 跨文档一致 / 长期规模 / 威胁建模二轮 / 双语 locale / 测试空洞 / 写作形象），40 条原始 → 30 去重 → 3 视角对抗验证，8 条确认全处置、22 条驳倒：

### Fixed
- **P1**：worklog-update Step 3 的 `diff -rq` 只报文件名，不构成 §12 信任模型宣称的人工审计点：补内容级审计（「有变更」skill 的 SKILL.md 与脚本逐个 `diff -ru` 展示再确认）；scan.sh 嵌套 roots（如 ~/code 与 ~/code/work）同仓重复扫描致 DIRTY 翻倍：改为全局收集 .git 路径 `sort -zu` 去重（临时文件不可写时降级逐 root，已知限制注明），嵌套双 root fixture 实测 1 个 REPO 块
- **P2**：README 双语补 maintain 能力（触发语表格行 + 状态段 M6 + 检查行口径升级为正误 + 体检五项）；PRD 头部状态刷新 v0.6 与 M6；init Step 4 与 PRD §16 如实告知 docs/ 暂为 zh 单语（en 无模板，翻译与 SKILL 全集同批决策）
- **P3**：settings.json `Bash(rm -rf:*)` 收窄为 `Bash(rm -rf .claude/skills/:*)`（最小权限一致性；验证者确认无增量安全收益、纯 hygiene，update 清理临时目录会多一次交互确认属可接受）；DEV.md 里程碑链补 M6

### Added
- tests：en locale wiki 模板直接过 lint 锚点检查的回归测试（捕捉 en 模板与 ANCHORS 表脱钩）

## Unreleased · vault 记忆维护（体检 + 修复，2026-07-12）

摄入时编译架构的盲区补批处理维护工序（PRD §18；设计参考 InquisiMind/digital-life 的维护工序思想）：

### Added
- `lint.py --health` 健康节：五项零 LLM 指标（状态漂移 / 孤儿页 / 实体分裂候选 / 膨胀 / TODO 年龄），阈值读 config `maintenance:` 段（全可选、内置默认值，schema_version 不升版保老 vault 零动作兼容）；退出码 0 健康 / 2 有待维护项；`--today` 供测试固定时钟；alias 存根（frontmatter `alias_of:`）与 `wiki/archive/` 不参与体检、`#todo/stale` 已分诊任务不重复报（保证体检可归零）
- ingest D.4 体检提醒行：超阈值才在当天日记末尾追加一行指引，健康时零痕迹；同日补充已有行则原地更新数字、清零改写不删行（日记只追加）
- `worklog-maintain` skill（本功能唯一新增，双 locale 路由）：现场体检 → 按腐坏类型分批修复每类一 commit → 全门验收出小结；授权跟触发方式走（交互 = 明示授权直接修，无人值守只报告）；三红线（diaries 永不触碰 / wiki 只合并归档重链 / TODO 僵尸只标记）
- 文档三小件：`docs/maintenance.md`（schedule 月度报告模式配方 + `~/.claude` memory 瘦身手工配方）、`docs/dev/deep-review.md`（深度 review 方法论占位，明确不产品化）
- tests/test_health.py 14 例；fixture vault E2E：五类腐坏注入 6 项全检出 → 5 类修复（6 → 1 → 0）→ 提醒行三路径 → 四门全绿

### Fixed（本功能对抗验证轮：6 维 21 条原始 → 19 去重 → 3 确认全处置、16 驳倒）
- 决策日志计数两处边界：### 子分组标题不再打断计数（只有一二级标题切段）；缩进子条目（理由 / 备注）不再计为独立决策
- 负数阈值（如 `todo_stale_days: [-5, 30]`）被静默接受并产出「超 -5 天」类误导输出：非法值忽略回退默认
- PRD §6.2 config 草案补 maintenance 段（穷举同步，配套记忆里的既知坑）

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
