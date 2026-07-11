# PRD · worklog-kit

> 立项：2026-07-11（周六）｜状态：v0.1 立项定稿，进入调优
> 本文档是产品需求 + 工程规格的单一真相源，由四轮孵化讨论 + 一轮 112 条多视角设计审计（4 路并行审计 97 条 + 完整性补漏 15 条）收敛而来。调优阶段直接修订本文档。

---

## 1. 背景与定位

worklog-kit 是 [personal-skills](https://github.com/iyuenan3/personal-skills) 中 `project-lifecycle.md` 方法论的**官方参考实现**：用一个「父项目」当大脑，管住一群项目从想法到退役的全生命周期。它把维护者私有的 worklog 工作流（Karpathy LLM Wiki 三层架构 + 睡前无人值守 ingest + 跨项目集体记忆）产品化成朋友可以直接 clone 使用的开源项目。

核心命题一句话：**把「接线」变成「配置」**。可复制的是方法论与工作流骨架（三层所有权、无人值守铁律、默认值表机制、提纯阶梯）；不可复制的专属接线（扫哪些目录、哪台远程机、IM 身份、个人 schema 细节）全部收进 config。

## 2. 用户画像

- 有 Claude Code 订阅，日常工作用 Claude + Codex
- 沟通工具为飞书（lark-cli 接入为一等模块）
- 会 git、会用终端
- 平台：macOS 为主，Linux 兼容；Windows 原生不支持，WSL 标注实验性

## 3. 产品原则

1. **clone 即用**：单仓模板，skill 内嵌 `.claude/skills/`，初始化一次当晚可跑
2. **冻结契约最小但完整**：skill 只依赖契约清单（§5），其余全部软性，鼓励用户像维护者一样自行演化 schema；产品版 schema 从 v0.1 的简洁度起步，不替用户预演化
3. **每个数据源都可失败**：不可达、鉴权过期、未挂载都是常态路径，降级记录一句继续跑，绝不挂起
4. **无人值守铁律**：触发消息即全部输入，永不阻塞提问，一口气跑到 commit
5. **隐私出厂即紧**：默认私仓 + 公开检测 + 凭证隔离 + 飞书最小记录，是默认行为不是文档建议
6. **冷启动即有内容**：第一晚就能看到成型的日记和非空的 wiki
7. **汇流口优先**：数据采集不追着设备跑，优先扫 git 远端 / IM / brain-dump 三个天然汇流口

## 4. 形态与仓库关系

### 4.1 仓库结构

```
worklog-kit/                      # 用户 clone / use-as-template 成自己的私有 vault
├── README.md                     # 产品叙事（project-lifecycle 简版 + 链接完整版）
├── CLAUDE.md                     # router（bootstrap 模式）
├── AGENTS.md                     # 指向 CLAUDE.md（防 Codex 打开 vault 时偏离约定）
├── AIREADME/                     # 极简预置（aireadme skill 可维护）
├── worklog.config.yaml           # 入 git：数据源 / 扫描根 / 时区 / 模块开关（无任何凭证）
├── worklog.config.local.yaml     # 不入 git：敏感字段（.gitignore 预置）
├── .claude/settings.json         # 权限 allow 清单（无人值守前提，不开 bypass）
├── .gitignore                    # 预置：状态文件 / 密钥类 / Obsidian 工作区
├── diaries/                      # 日记层（只追加）
├── wiki/                         # 知识层（LLM 维护）：index.md + log.md + todos.md + projects/
├── inbox/                        # 素材收件箱：人放原料、AI 消化
└── .claude/skills/
    ├── worklog-init/             # 初始化：环境预检 + config 生成 + 三件套安装 + 冷启动
    ├── worklog-ingest/           # config 驱动通用版（核心工程，重写非删改）
    ├── worklog-import/           # markitdown 素材摄入（init 存量迁移复用）
    ├── feishu-setup/             # lark-cli 安装 + 认证 + 坑文档
    ├── worklog-query/            # 「查 X」显式化
    ├── worklog-lint/             # 断链 / frontmatter / 凭证扫描（标点门为中文可选项）
    └── worklog-update/           # 从 upstream 拉 skill 新版（安全边界见 §12）
```

### 4.2 与 personal-skills 的关系

- **kit 不 vendor 全局三件套**（aireadme / stash / pitfalls），避免「私有版 → personal-skills → kit」三向同步漂移
- `worklog-init` 初始化时从 personal-skills 拉三件套装到 `~/.claude/skills/`（只 cp 三个目标子目录，不暴露整仓），并经用户确认后把 pitfalls「高危活前先查」全局纪律行追加进用户 `~/.claude/CLAUDE.md`（追加前检查该行是否已存在，绝不覆盖已有内容）
- personal-skills 打 **release tag**，kit 锁定 tag 不追 HEAD；升级三件套是显式操作
- `project-lifecycle.md` 留在 personal-skills 作完整方法论，kit README 写简版叙事并链接
- personal-skills README 中 worklog-ingest 条目从「不建议直接使用」改为指向 kit（发布时同步）

## 5. 冻结契约（v0.1）

skill 只依赖以下各项，模板全部预置，`worklog-update` 永不触碰其中的用户数据：

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
| 5 | vault 内部状态 | 内置 | memory 目录 mtime + wiki / diaries 改动感知（审计补足：这是 ingest 自身状态源，不属于外部四层） |

飞书（feishu via lark-cli）作为 IM 协调源与上表并列，见 §9.4。

### 6.2 config 草案

```yaml
schema_version: 1
timezone: Asia/Shanghai          # 默认，init 时询问
day_boundary: "07:00"            # 日期分割线，可配（00:00 至分割线归前一天）
language: zh                     # 写作规范 / 标点门按此切换
identities: [me@personal.com, me@company.com]   # 多署名过滤，init 从 git config 预填
sources:
  - {type: github, account: xxx, assume: active}
  - {type: local-git, roots: [~/projects, /Volumes/T7/work], assume: active}
  - {type: remote-ssh, host: workbox, assume: active, on_unreachable: note}
  - {type: feishu, via: lark-cli, on_unreachable: note, record_others: false}
modules:
  life_section: true             # 日记「生活」段可选
diary_title_template: "# 工作日记：{year}年{month}月{day}日（{weekday}）"
```

`worklog-init` 交互问的不是「你的项目在哪」，是「**你的工作都发生在哪**」，逐个生成 source；日记项目段标注来源（扫描 vs 口述）。

## 7. Skill 需求要点

| skill | 关键需求 |
|---|---|
| worklog-init | 环境预检（git user.name/email、remote 与 push 鉴权 dry-run、gh auth、uv、OS 检测且 Windows 原生直接报错退出）；仓库 visibility 检测（非 private 红色警告并暂停）；config 交互生成（时区 / 分割线 / 身份 / 数据源）；三件套安装（§4.2，已存在则比对提示覆盖 / 跳过）；冷启动（§10）；完成后生成 GETTING_STARTED.md（.gitignore 内） |
| worklog-ingest | 见 §8 |
| worklog-import | `uvx markitdown` 转换 docx / PDF / pptx 等入 `inbox/`；图片 LLM 描述默认关；ingest 不自动扫 inbox（防耗时爆炸），只引用当天新增条目 |
| feishu-setup | 指引安装官方 `@larksuite/cli`（npm，已确认非自维护）；认证 walkthrough；坑文档（Keychain 降级、`bash -lc` 加载 node、token 约周级过期）；授权失败即在 config 禁用 feishu 源并明确告知 |
| worklog-query | 「查 X」跨日记 + wiki 检索行为显式化 |
| worklog-lint | 通用项：断链、frontmatter 完整、凭证扫描（含截断 token 前缀）；中文可选项：标点门（punctuation_check.py 随包，`language: zh` 才加载）；个人演化项不进 kit |
| worklog-update | 只 rsync `.claude/skills/` 白名单路径，其余 hard deny（§12） |

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

**降级矩阵（每源必答两问：连不上怎么办 / 鉴权失效怎么办）**：全部走「记一句 + 继续 + 晨起报告列清单」，飞书 token 过期额外提示重 auth 命令。

**git 安全三件**：开跑先 `git pull --ff-only`（失败不 rebase 不 merge，降级记录）；`.ingest.lock` 并发锁；Edit 锚点找不到时 fallback 为 append 文件尾 + status 记一行（兼容用户已演化结构，绝不报错中断）。

## 9. 安全与隐私（出厂默认）

1. **权限**：模板随附 `.claude/settings.json`，allow 清单精确列出 ingest 用到的命令模式（git / ssh / python3 / find / date 等），不开 bypassPermissions；README troubleshooting 写明首跑弹权限的处理
2. **公开仓双检**：init 时 + 每晚 push 前 `gh api` 查 visibility，发现 public 立即中断 push 并红色警告（use-as-template 误选 public、日后手动改公开都在此拦截）
3. **凭证隔离**：config 两层（base 入 git 零凭证 / local 不入 git）；.gitignore 预置 `.ingest-status.md`、`.ingest.lock`、`worklog.config.local.yaml`、`.obsidian/workspace*`、`.env*`、`*.key`、`*.pem`、`id_rsa*`、`credentials*`、`GETTING_STARTED.md`、`.DS_Store`
4. **飞书最小记录**：默认只记用户本人发的消息（从维护者个人纪律升级为出厂默认），记录他人需显式 `record_others: true` 且 README「飞书数据使用须知」写明合规责任（被记录同事、雇主信息安全政策、私仓仍在第三方服务器）；不臆断对方确认、清单类逐字照录等纪律进 skill 本体
5. **数据所有权**：diaries / wiki 是标准 markdown；提供 worklog-export（去 Tasks 语法 + wikilink 转普通链接）作退出通道

## 10. 冷启动与首周体验

- **日记侧**：init 回填最近 **3 天简版**日记（概览 + 时间线 + commit 列表，不跑完整 judgment，标注「自动回填、信息有限」）；天数可选。否决项：14 天全量回填（数小时 + 数百万 token，首日体验反噬）
- **wiki 侧**：worklog-import 批量转换用户存量文档入 inbox/，第一天打开不是空库
- **首周**：GETTING_STARTED.md 教第一晚 brain-dump 怎么说、次晨如何用「更新日记」订正、说明前三天是磨合期 + 首跑 FAQ

## 11. 可观测性

`.ingest-status.md`（卡点与自救命令，成功时标 last-success）+ `.ingest-history.log`（运行流水）+ Step E 晨起报告（含降级源清单、未附带信息提示）。

## 12. 升级与兼容

- worklog-update 安全边界：只同步 `.claude/skills/` 下白名单文件，绝不 `git merge` upstream，绝不触碰 diaries / wiki / config
- config `schema_version`：skill 启动断言版本，update 后不匹配则输出需补字段 + 默认值；版本过旧给明确报错不静默异常
- 三件套锁 personal-skills release tag，升级显式触发
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
- plugin 市场分发（用户 >5 再评估）
- aireadme STANDARD.md 全文英文化（用户画像全中文，后置）

## 15. 里程碑

- **M1 模板骨架**：仓结构 + 契约文件全套预置 + settings.json + worklog-init（预检 / config 生成 / 三件套安装）
- **M2 ingest 重写**：§8 全部 + scan.sh 可移植版（BSD / GNU 通用写法：`touch -t` + `find -newer`，不用 `date -v` / `-newermt`；每 root 扫描超时保护）
- **M3 连接器**：github 收集器 + feishu-setup + worklog-import
- **M4 收尾**：query / lint / update + README 产品叙事 + GETTING_STARTED + CI（shellcheck + punctuation_check pytest）+ 极简 CONTRIBUTING 与 issue 模板
- **M5 pilot**：两位朋友试用（一个飞书重度 + 一个纯本机），企业飞书授权实测，按摩擦迭代

## 16. 开放问题

- pilot 人选待定
- 发布时机与仓库可见性：公开前须过对抗式泄漏审计（含本 PRD 与 git 全历史）
- personal-skills release tag 首版版本号

## 17. 依赖与许可

- lark-cli = 飞书官方 `@larksuite/cli`（npm），文档指引安装，不随包分发
- markitdown = microsoft/markitdown（MIT），经 `uvx` 调用
- gh / glab（按需）、uv、python3、bash 3.2+（scan.sh 兼容目标）
- 本仓 License：Apache-2.0（与 personal-skills 一致）
