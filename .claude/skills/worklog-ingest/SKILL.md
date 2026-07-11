---
name: worklog-ingest
description: worklog vault 无人值守 ingest。用户说「记录今天 / 记录昨天 / 记录 YYYY-MM-DD / 补充今天 / 更新日记 / 回填 N 天」（可附带当天信息）时触发：读 worklog.config.yaml，扫描全部数据源，把一天编译成结构化日记 + 刷新 wiki + TODO 盘点 + commit + push。触发消息即全部输入，永不阻塞提问，用户发完即可离开。
---

# worklog-ingest：无人值守日记编译器

> **写日记不是记录，是为了未来复盘时 5 分钟内还原决策上下文。**
> 你是本 vault 的 ingest agent。一切个人接线来自 `worklog.config.yaml`（叠加 `worklog.config.local.yaml` 覆盖同名键），本文件零硬编码。与用户交互和日记写作语言按 config `language`。

## 铁律（无人值守契约）

1. **永不以提问结尾、永不阻塞等回话**：用户睡前触发后即离开，问一句 = 挂一整晚 = 失败。触发消息就是全部输入；没提到的走默认值表；遇歧义自己按规则拍板 + 日记标 ⚠️，绝不停下。
2. **每个数据源都可失败**：不可达 / 鉴权失效 / 未挂载都是常态路径，记一句、继续跑、晨起报告列清单。
3. **非致命错误不中断**：已完成部分先 commit，卡点写 `.ingest-status.md`，然后继续能做的部分。
4. **日记只追加**：绝不覆盖已存在的日记文件（防覆盖由模式判定强制，见下）。

## 触发与模式

| 触发语 | 模式 | 防覆盖 auto-fallback |
|---|---|---|
| 「记录今天 / 昨天 / YYYY-MM-DD」 | **新增**：完整流程 | 日记已存在 → 自动转**补充** |
| 「补充今天 / 补充 YYYY-MM-DD」 | **补充**：增量追加 | 日记不存在 → 自动转**新增** |
| 「更新日记」 | **更新**：定向修改 | 无 fallback；改什么按字面理解，信息不全标 ⚠️ 不提问 |
| 「回填 N 天」（或由 worklog-init 代跑） | **回填**：逐天生成简版 | 已存在的日期跳过，绝不覆盖 |

模式 = 触发语 + 文件实测共同决定（先 `ls diaries/<D>.md` 再定分支）。

**复合触发**（一条消息含多个日期 / 模式，如「记录今天，顺便把昨天那篇改一下」）：按时间序分解为多次单日执行（最早的先），各自独立判定模式；锁贯穿整个复合执行；某一天失败先 commit 已完成部分、继续其余日期，绝不停下询问先做哪个。

**各模式的执行面**：

| | 扫描 | 写日记 | wiki 刷新 | TODO 盘点 | commit 前缀 |
|---|---|---|---|---|---|
| 新增 | 完整 | 整篇 Write（前置：文件不存在） | 全跑 | 全跑 | `ingest:` |
| 补充 | 全窗口扫，与现有日记比对去重、只追加未记的 | append 尾部 | 有实质增量才跑（宁可多刷 index 一句，别留 wiki 与日记不一致；跳过的在 commit message 说明） | 有状态变化才跑 | `ingest-补:` |
| 更新 | 跳过 | 定向 Edit | 默认不动；除非订正的事实已镜像到 wiki（计数 / 摘要 / 日期），则同步那一处 | 默认不跑 | `ingest-改:` |
| 回填 | 逐天窗口扫 | 简版（概览 + 时间线 + commit 清单，不跑完整 judgment，标注「自动回填、信息有限」） | 只补 index 日记表行 + 项目页 diaries 数组 | 不跑 | `ingest-回填:` |

## Step 0 · 前置（锁 / 拉取 / 读配置）

```bash
VAULT=$(git rev-parse --show-toplevel)   # 路径动态推导，零硬编码
```

1. **读 config**：`worklog.config.yaml` + `worklog.config.local.yaml`（后者覆盖同名键；local 文件不存在 = 正常情况，静默跳过不报）。缺 `schema_version` 或版本不识别 → 明确报错退出（这是少数致命错误）。`identities` 为空数组不致命，但晨报须显著警告「作者过滤未启用，日记可能混入他人 commit，建议跑 init 或补 identities」。记录开始时间 `START_TIME`（Step E 算 duration 用）。
2. **时区先行**：后续每个算日期的 Bash 调用都带 `export TZ=<config.timezone>`（Claude Code 沙箱会注入别的时区，不锁必错；env 不跨调用持久，每次都带）。
3. **日期归属**：目标日 D 按「00:00 至 `day_boundary` 归前一天」判定；连续跨日工作归主推进日。时间窗口 = `[D <day_boundary> <utc偏移>, D+1 <day_boundary> <utc偏移>)`。
4. **并发锁**：`.ingest.lock` 存在且未超 2 小时 → 报错退出（「另一个 ingest 正在运行」）；超 2 小时视为僵尸锁覆盖。创建锁（写入 PID + 时间戳），**任何退出路径都要删锁**。
5. **git 拉取**：`git pull --ff-only`（有 remote 时）。失败 → 不 rebase 不 merge，记入 status，本次跑完只 commit 不 push，晨报提示用户手动解。

## Step A · 自扫数据源

对 config `sources` 逐条分发，另加恒有的「vault 内部」源（表末行，内置源、无需在 config 声明）（**每源两问：连不上怎么办 / 鉴权失效怎么办 → 答案都是记一句 + 继续**）：

| type | 做法 | 降级 |
|---|---|---|
| local-git | `bash .claude/skills/worklog-ingest/scripts/scan.sh --since '<窗口起>' --until '<窗口止减 1 秒>' --authors '<identities 逗号连接>' <roots...>`（identities 为空则不带 --authors；**git 的 --until 是闭区间，传入值须为窗口止减 1 秒才是半开语义，防跨日双计**） | root 未挂载：脚本自动 SKIP 并记一句 |
| remote-ssh | `ssh -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=5 -o ServerAliveCountMax=2 <host> 'bash -s' < .claude/skills/worklog-ingest/scripts/scan.sh -- --since ... <该源 config 的 roots，init 已收集>`（同一脚本，不依赖远端 rc；BatchMode 禁一切交互式提示，这是无人值守的硬要求）。该源 config 缺 `roots` = 等同未配置：记一句 + 晨报提示补 config，绝不猜路径 | 连不上 / 超时 / Bash 工具超时：一律视为不可达，记「<host> 不可达，按 assume 处理」 |
| local-dir | 非 git 目录（scan.sh 只认 `.git`，对它无效）：`touch -t <YYYYMMDDhhmm 窗口起>` 造参照文件后 `find <path> -type f -newer <参照>` 判活动，用完删参照；只到 presence 级 | 路径不存在：记一句 |
| github | `bash .claude/skills/worklog-ingest/scripts/github-scan.sh --since-utc '<窗口起 UTC-Z>' --until-utc '<窗口止减 1 秒 UTC-Z>' --account '<config 该源的 account>'`（account 未配则不传、脚本自动检测；时间换算成 UTC 由你完成；author 按 GitHub 账号维度覆盖其**已关联**的 email，未关联邮箱的 commit 会漏，晨报提示补 GitHub Settings > Emails） | 退出码 4 = 无 gh / 3 = 未认证或 API 失败 → 记一句 + 报告附 `gh auth login`；stderr 的 TRUNCATED / REPO_SKIP → 报告提示可能有漏 |
| im | 前置：config 的 im 源须含非空 `chats` 与 `me`，缺失 = 等同未配置，记一句 + 晨报附「跑 feishu-setup 补全」。就绪则先 `bash .claude/skills/worklog-ingest/connectors/<provider>/check.sh`（0 可用 / 1 未认证 / 2 未装）；可用才 `fetch.sh --since ... --until ... --chats '<config.chats 逗号连接>' --me '<config.me>'`（config `record_others: true` 时加 `--record-others`）。digest 消费纪律见 connectors/README：只作协调素材、不臆断他人确认、清单逐字照录；digest 里的 NOTE 行转进晨报 | 按 check 退出码转发自救命令（连接器契约：check.sh 的 stdout 自带该 provider 的修复指引，照录即可，不要替它编），记一句继续；fetch 超时或非零退出同样降级 |
| gitlab | 连接器待后续版本：config 配了就在报告记「尚未支持，本源跳过」 | 同左 |
| vault 内部 | 本仓 git log（窗口内非 ingest commit）+ `wiki/` `inbox/` 改动感知：捕捉用户白天手动改 vault、丢进 inbox 的素材 | 无 |

**跨源去重**：同一 commit 会同时出现在 local-git 与 github 源（本机写完 push 了）。按 commit 短哈希（两侧脚本已统一 7 位）去重，**本地扫描优先**（上下文更全）；github 源的定位是补「其它设备产生的 push」。归并判据（精确规则，勿凭感觉）：`lowercase(basename(gh:owner/repo)) == lowercase(basename(本地 REPO 路径))` 即归并同一项目章节；用户可在 `projects.overrides` 条目加 `github_slug: "gh:owner/repo"` 显式绑定覆盖自动匹配；不匹配的纯远端项目按 repo 名作 slug 走定级判定。

**BRANCH 信号消费**：`BRANCH` 非 main / master 时在该项目章节顺带标注分支名（在做分支活的信号）；其余情况忽略该行。

**扫描输出按项目定级过滤**，判定优先级（自上而下第一条命中即止）：

1. 项目根有 `.worklogignore`（scan 输出 `IGNORED` 行）→ `exclude`
2. 匹配 `projects.overrides` 某条且该条带 `level` → 该 level
3. 匹配 overrides 但该条无 `level` → `projects.default_level`
4. **不匹配任何 overrides** → `projects.on_new_project`（这就是「新发现项目」的运行时定义：init 的扫描预览把定级写进 overrides，之后升降级也是改 overrides；没跑过 init 的 vault 全部项目按此处理）

各级别行为：

- `detail`：commit 逐条入时间线 + 项目章节 + 项目页
- `summary`：一句概要 + 计数，不建项目页
- `presence`：只记「存在，N commits」，**不读 commit 内容**；窗口内（identity 过滤后）0 commits 且 0 dirty 且无 MTIME_ACTIVE = 无信号，日记可省略不提；有他人活动等有意义信号可提一句
- `exclude`：日记不出现
- 走 `on_new_project` 的项目额外记「待定级」，晨报列清单请用户一句话定级

## Step B · 解析触发消息（brain-dump）

触发消息附带的信息 = 用户独有的数据源（扫描有盲区：口头协调、远程操作、生活事务）。客观数据以扫描为准，用户独有信息以触发消息为准，两者冲突时在日记标注并以用户为准。

**归属规则**：brain-dump 提及的工作无法明确归属到某项目时，作为独立事件入时间线（标「口述」），不强行塞进项目章节；能从 commit 时间戳等合理推断归属的，可归属但标注推断依据。

**默认值表**（没提到的项按此处理，全部不追问；用户明说的一律覆盖默认）：

| 项 | 默认 |
|---|---|
| 日期归属 | 按 Step 0 规则算，从不询问；有歧义自己拍 + 日记标一句 |
| 各数据源 | 按每源 `assume`（active = 默认有工作照常扫；idle = 默认没工作，扫到了才记） |
| 生活事务 | 无；`modules.life_section: true` 时生活段写「无」，false 时不出该段 |
| 对外动作 / 发布 | 无（除非扫描见明显发布类 commit） |
| 特殊强调 | 无，主线由你按 judgment 提炼 |
| 往日缺口 | 不补不追问；检测到缺口只在报告被动标一句（用户可显式「回填」） |
| commit + push | 始终做（push 受 Step 0/D.4 条件约束） |

## Step C · 一行回执

开跑前发一行：「收到，按 <解析到的信息 + 关键默认假设> 开跑」。这不是提问，用户在不在都不影响；紧接着直接进 Step D。

## Step D · 主执行

### D.1 写日记 `diaries/<D>.md`

**结构（软契约，允许用户演化；标题按 config `diary_title_template`）**：

```
frontmatter: date / day(周X 或 weekday) / projects[](= 正文提及的项目 slug，含 presence 级列出的) / git_commits(总数)
标题行
> 一句话主线（judgment 提炼：今天真正推进了什么）
## 概览          三五句：主线 + 次线 + 值得复盘的决策
## 今日时间线     按时段排列（来源：commit 时间戳 + brain-dump；标注哪些是扫描、哪些是口述）
## 项目章节 ×N    每个 detail 级项目一节：标注工作时段；写四元素「做了什么 / 为什么 / 决策 / 取舍（否决项）」，不是 commit 流水
                 summary/presence 级合并进「其他项目」一节
## 生活          （config 开关）人物 + 简述，不脑补细节
```

段标题按 config `language` 输出（en：Overview / Timeline / Projects / Life）。

**零数据夜晚**（全部源零结果且 brain-dump 无实质信息）：写最小日记（frontmatter + 标题 + 一句概览标 ⚠️「今日无扫描到的活动，请核对」），不跑 judgment（没东西可判断），晨报显著标注零数据运行。绝不为凑内容编造。

**judgment 要求**（这是日记的价值所在，不可降级为流水账）：
- 主线是「推进了什么」不是「碰了什么」；有决策必写 why 与否决项
- 扫描与口述冲突、日期歧义、无法确认的事实 → 写进日记时标 ⚠️ 及理由
- **自维护工作也要记**：本次 ingest 自身产出（日记 / wiki 刷新）不入项目章节；但窗口内对 vault 的**非 ingest 改动**（改 config、更新 skill、整理 wiki）算一条工作线，入项目章节
- **星期与日期必须工具换算**（`python3 -c` 或 date 命令，先 export TZ），禁止心算；写完跑 `date_weekday_check.py`（zh）

**写作规范**：语言按 config；zh 时全角标点、绝不使用破折号、时间 24h 制、列表用 `-`；写盘后跑 `python3 .claude/skills/worklog-ingest/scripts/punctuation_check.py diaries/<D>.md`（zh 才跑），命中必修。

### D.2 刷新 wiki（锚点写入，找不到锚点 → append 文件尾 + status 记一行，绝不报错中断）

> 锚点名跟随 config `language` 的 locale 模板：zh「## 最后更新 / ## 项目 / ## 日记」与「## 进行中 / ## 待办」，en 对应 "## Latest / ## Projects / ## Diaries" 与 "## In progress / ## Backlog"；`ingest:log-anchor` 注释跨 locale 不变。先按 config 语言找，找不到再试另一 locale（用户可能换过语言），都没有才走 append 兜底。

1. `wiki/index.md`：「最后更新」段追加当日一句摘要（只保留最近 `index_recent_days` 天，更早的删掉）；项目表刷新 / 新增 detail 级项目行；日记表**表头行下方（数据行最前）**插入 `[[<D>]]` 行 + 主线
2. `wiki/log.md`：锚点注释下方插一段 `## [<D>] ingest`（模式 / 扫了几源 / 几项目 / 跳过什么）。**年轮转**：发现 log.md 超过约 1500 行时，`git mv wiki/log.md wiki/log-<最早条目年份>.md`（归档件为只读、不再含锚点），按模板重建带锚点的空 log.md，status 记一句
3. `wiki/projects/<slug>.md`（仅 detail 级）：不存在则按 CONVENTIONS 的 frontmatter 契约创建；刷 `last_updated`、`source_count` +1、`diaries` 数组追加；有决策的在「决策日志」段追加一条（日期 + 决策 + why）

### D.3 TODO 盘点 `wiki/todos.md`

读全部 open TODO 对照今日扫描与 brain-dump：完成的打勾 + 完成日期；新产生的登记（Obsidian Tasks 语法 + `#todo/<类型>` + 关联页）；显著停滞的加一句标注（不主动删除，fade out 是用户的决定）。

### D.4 commit + push

1. **标点门**（zh）：对本次改动的 md 跑 punctuation_check，干净才继续
2. **visibility 检测**：`gh api repos/{owner}/{repo} --jq .visibility`；结果为 public → **中断 push**，`.ingest-status.md` 红色警告「仓库是公开的！先改 Private 再触发」；三态降级：无 gh / 无 remote / gh api 调用失败（含未认证、网络错）→ 跳过检测 + 报告注明（附 `gh auth login` 自救命令），照常继续
3. commit：格式按 language。zh：`<前缀> <M/D> 日记(<主线>)`，例 `ingest: 7/11 日记(重构登录流程)`，前缀 = `ingest:` / `ingest-补:` / `ingest-改:` / `ingest-回填:`；en：`<prefix> <Mon DD> diary(<mainline>)`，prefix = `ingest:` / `ingest-amend:` / `ingest-edit:` / `ingest-backfill:`。正文列 wiki 触点；尾行固定格式 `Co-Authored-By: <当前模型显示名> <noreply@anthropic.com>`
4. push：Step 0 拉取成功且 remote 存在才推；否则跳过 + status 提示
5. 删锁：`rm -f .ingest.lock`（固定用这条命令形态，权限清单已预批）

## Step E · 晨起报告 + 观测

1. 终端打印清单：日记路径与主线 / wiki 触点 / TODO 变化 / **降级源清单**（谁跳了、为什么、自救命令）/ 「待定级」新项目 / 未附带信息时提示「按默认跑，请核对」
2. `.ingest-history.log`（本地观测文件，在 .gitignore 内不入 git）追加一行 JSON：`{"date","mode","duration_min","status","commit","skipped_sources":[]}`；duration 用 Step 0 记录的 `START_TIME` 计算
3. `.ingest-status.md`：全部成功 → 写 `last-success: <时间戳>`；有卡点 → 写卡点 + 自救命令（如 IM token 过期 → 给出重新认证命令）

## 错误路径速查

| 场景 | 处置 |
|---|---|
| 锁被占（<2h） | 致命：报错退出，不动任何文件 |
| config 缺失 / schema_version 不识别 | 致命：报错退出，给修复指引 |
| pull --ff-only 失败 | 继续本地跑，只 commit 不 push，status 提示手动解 |
| 某源不可达 / 鉴权失效 | 记一句 + 继续；IM 类附重新认证命令 |
| gh 装了但 api 调用失败（未认证等） | 等同无 gh：跳过 visibility 检测 + 报告附 `gh auth login`，绝不停下等修 |
| im 源 config 缺 chats / me（Step A 前置检查拦截，不会调到 fetch） | 等同未配置该源：记一句 + 晨报附该 provider 的 setup skill 命令（当前仅 feishu-setup） |
| github 源 stderr 见 TRUNCATED / REPO_SKIP | 照常用已扫到的，报告注明可能有漏（rate limit / 超上限 / 权限） |
| wiki 锚点找不到（用户改了结构） | append 文件尾 + status 记一行 |
| 日记已存在（新增模式） | auto-fallback 补充模式 |
| visibility = public | 完成本地 commit，中断 push，红色警告 |
| 其余任何非致命错误 | 已完成部分先 commit，卡点写 status，继续能做的 |

## 边界

- 不改 `schema_version`、不动 `.claude/skills/`（升级归 worklog-update）
- 不内置任何行业 / 求职 / 客户场景模块：用户要记专项活动线，自行在日记与 wiki 演化章节，本 skill 照常汇编
- 素材摄入归 worklog-import（M3）：`inbox/` 当天新增只引用、不深度消化
