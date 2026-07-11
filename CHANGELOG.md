# Changelog

worklog-kit 版本史。格式参考 [Keep a Changelog](https://keepachangelog.com/)。

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
- 四视角对抗验证（38 条发现）修复：en locale 补齐全套产品件（CLAUDE / AGENTS / AIREADME 12 件 / config）；settings.json 补 init 全部所需命令；stash 英文 How-to-apply 校验补 bold 口径；discover.sh 发现深度默认 4（修 off-by-one）并 prune 隐藏目录与 node_modules；worklog-init 修 GETTING_STARTED 路径 / WSL 辨识 / gh auth 预检 / 无 remote 分支 / overrides 格式规范；skill README 安装后断链改绝对 URL；config 增 `index_recent_days`
