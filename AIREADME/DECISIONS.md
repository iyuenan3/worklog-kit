# DECISIONS（append-only）

> 每条 = 编号 + 日期 + `Problem / Constraint / Decision / Alternatives(否决) / Tradeoff`。schema 演化（改 wiki 结构、改日记章节、改 config 语义）在此记理由，让半年后的你读得懂当初为什么。

## D1 · 2026-07-13 · 多仓映射到项目页：嵌套/并列仓各自独立成项（不归并父页）

- **Problem**：一个项目目录下常有多个 git 仓（嵌套子仓、submodule、并列的 frontend/backend）。PRD §6.4 原写「嵌套子仓默认归并父项目页」，但采集脚本从建成起就是「每个 `.git` 一个独立项目单元」，归并逻辑从未实现，文档承诺与行为相反。
- **Constraint**：采集层（scan.sh 行协议）已按「各自独立一段」输出；归并要在编译层重建父子关系，且「哪些算一个项目」因人而异、没有通用判据。
- **Decision**：改口认账实现语义，嵌套/并列仓一律各自独立成项、各建各的 wiki 项目页。要把整棵树当一个项目看，用 `projects.overrides` 的 glob 批量定级（`~/x/parent/**`）；真需要「多仓合并成一页」列为后置开放问题（PRD §16）。
- **Alternatives（否决）**：① 实现归并父页，否决理由：判据不可通用化，且会让 slug↔页 关系随「今晚扫到哪些仓」漂移。② 保留 PRD 原承诺不动代码，否决理由：文档持续失实，误导使用者。
- **Tradeoff**：并列多仓（frontend + backend）的用户视角「一个项目」被拆成多页；换来语义简单、与采集层一致、无漂移。

## D2 · 2026-07-13 · 项目页 `path:` 锚点：同名项目消歧的持久身份

- **Problem**：slug = 目录名，跨 root 同名项目（`~/a/webapp` 与 `~/b/webapp`）会争同一个 `webapp.md`。仅靠「同晚扫描是否撞名」瞬时判定消歧，会让同一项目在「撞名夜/独处夜」之间在裸名与消歧名间摇摆，产出实体分裂的双页。
- **Constraint**：项目页 frontmatter 契约原本只有 last_updated / source_count / diaries，无路径身份，「这页属于哪条路径」永远不可判定。
- **Decision**：项目页 frontmatter 增可选 `path:` 字段作持久锚点。定 slug 三步：先查 `path:` 锚点沿用其 slug → 无撞名用 basename → 撞名则叠加父目录段消歧并写入 `path:`。`.worklogignore` 同批升级为否决整棵子树（否则独立成项后树顶标记罩不住子仓）。
- **Alternatives（否决）**：① overrides 加 slug 键，否决理由：定级与命名两套键增负担，且 override 是可选的、覆盖不全。② 无锚点靠每晚重算，否决理由：即 Problem 本身。
- **Tradeoff**：项目页多一个可选字段；换来跨夜稳定身份，消除 lint --health 本要抓的实体分裂腐坏。
