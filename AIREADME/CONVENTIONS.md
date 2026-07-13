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
- TODO 用 Obsidian Tasks 语法记在 `wiki/todos.md` 分区（非 Obsidian 环境同样成立，见该文件头注）
