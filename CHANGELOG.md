# Changelog

worklog-kit 版本史。格式参考 [Keep a Changelog](https://keepachangelog.com/)。

## Unreleased · M2 ingest 通用版

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
