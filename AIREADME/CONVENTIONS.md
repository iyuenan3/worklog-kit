# CONVENTIONS

## 日记（最小契约）
- 文件：`diaries/YYYY-MM-DD.md`；标题按 config `diary_title_template`
- 归属：00:00 至 `day_boundary` 归前一天；时区按 config `timezone`
- 结构软性：除文件名与「只追加」外，章节结构可自行演化（演化了记 DECISIONS）

## wiki 项目页 frontmatter（契约，ingest 每晚刷新）

    ---
    last_updated: YYYY-MM-DD
    source_count: N          # 提及本项目的日记数（复利指标）
    diaries: ["[[YYYY-MM-DD]]", ...]
    path: /abs/path          # 可选：slug 消歧锚点（同名项目并存时由 ingest 写入，跨夜稳定身份）
    ---

## 项目记录级别（config projects）
detail（详记 + 建项目页）/ summary（一句概要）/ presence（只记存在与计数）/ exclude（不出现）；项目根或任一祖先目录放 `.worklogignore` = 永久 exclude（否决整棵子树，嵌套子仓 / submodule / worktree 同享）。

## 写作
- 语言按 config `language`；zh 启用中文标点一致性检查（标点门）

## TODO 系统（Obsidian Tasks 语法，非 Obsidian 环境优雅降级为普通文本）
- 语法：`- [ ] 描述 #todo/<类型> [[关联页]] 📅 YYYY-MM-DD`；完成 `- [x] … ✅ YYYY-MM-DD`、失效 `- [x] ~~描述~~ ❌ 失效 YYYY-MM-DD`（完成与失效都勾 `- [x]` 闭合，聚合 query 的 `not done` 才不回流）。每条真 TODO 必带 `#todo/<类型>` 标签。
- 主存储：跨项目 / 元任务记在中央 `wiki/todos.md` 的 `## 进行中` / `## 待办` 分区；用户可自行演化（如把项目专属 TODO 记到项目页），那里的完成项原位留作决策日志上下文、不搬。
- 完成即归档：ingest 每次把中央 `wiki/todos.md` 本次标 ✅ / ❌ 的完成项扫到末尾 `## 📦 已完成归档` 段（一句结论 + 日期），主存储恒只剩活跃项；归档 sweep 只作用于中央 todos.md。
- 视图永不物化：「当前有哪些待办」是 Claude 会话输出（ingest 收尾清单 + 平时「列出待办」现算现给），不写成 todos.md 里的固定段。文件只存储（主存储分区 + `## 📦` 归档 + 可选 Obsidian 聚合 query），要看看板就问 Claude；这样非 Obsidian 环境无需那段死 query 也能用。
- 盘点先挖证据：判 TODO 状态别只看 checkbox 文字，先读关联项目 git log 与项目记忆核对进度再判，标完成必列证据（见 ingest D.3 与 maintain）。
- 聚合 query 坑：Obsidian Tasks 聚合 query 一律正向收口 `tags include #todo`（只抓带 `#todo` 标签的项），配 `tags do not include #todo/stale` 与 `path does not include diaries/`。只按 path / stale 负向过滤会把迁移 playbook、归档件、文档里的 `- [ ]` 示例等非 TODO 的 checkbox 全捞进看板；非 TODO 的 checkbox 天然无标签、正向收口自动排除。`sort by` 每行只写一个字段。
