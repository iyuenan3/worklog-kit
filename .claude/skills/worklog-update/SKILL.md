---
name: worklog-update
description: 从 upstream worklog-kit 拉取 skill 新版。用户说「升级 skill / 更新 worklog-kit / update skills」时触发：锁定 release tag 拉取、逐 skill 展示差异、经确认后只同步 .claude/skills/，绝不触碰用户数据；随后做 config schema 与 wiki 锚点兼容检查。
---

# worklog-update：skill 升级器

> 与用户交互的语言跟随其消息语言。**安全边界（hard deny）：只写 `.claude/skills/` 白名单路径。`diaries/` `wiki/` `inbox/` 两层 config、`AIREADME/`、根文档一律不碰；`.claude/settings.json` 只展示 diff 供用户手动决定。**

## 前置

- `.ingest.lock` 存在 → 拒绝运行（等 ingest 跑完）。
- upstream 默认 `https://github.com/iyuenan3/worklog-kit`（config 顶层键 `upstream_repo` 可覆盖，适配 fork 用户；模板注释里有示例）。

## 流程

1. **取版本**：`git ls-remote --tags <upstream>` 取最新 release tag；无 tag（上游 pre-release 期）→ 用 main 并明确告知「非 release 版本，风险自担」。
2. **浅克隆到临时目录**：`git clone --depth 1 --branch <tag> <upstream> <scratch 临时目录>`（绝不 `git remote add` / `git merge`，上游历史不进用户仓）。
3. **差异盘点**：白名单 = 上游 `.claude/skills/` 下全部子目录。逐 skill 与本地 `diff -rq`，列出 新增（上游新 skill，供用户选择装不装）/ 有变更（**明确列出「本地存在但上游已删」的文件**，镜像同步会删掉它们）/ 本地独有 skill（用户自己加的，永不动）；摘录上游 CHANGELOG 相关段给用户看「这次更新带来什么」。
4. **确认后同步**：逐 skill（或用户说全部）做**镜像同步**：`rm -rf .claude/skills/<name>/ && cp -R <上游对应目录> .claude/skills/<name>/`（纯 cp -R 是追加语义，上游删掉的旧文件会残留成半套状态）。用户在该 skill 目录内自加过文件的，在 Step 3 已看到删除清单、确认才动；本地独有 skill 与一切用户数据不动。注意：worklog-lint 与 worklog-ingest 共享校验脚本（标点门 / 日期门在 ingest 目录），两者**建议成对升级**。
5. **config schema 检查**：比对上游模板 `worklog.config.yaml` 的 `schema_version` 与本地：上游更新则**列出需补的键 + 默认值**。实施口径：只自动追加**顶层键**（含注释，插在文件末尾）；嵌套键（modules 子键、sources 条目属性）以 diff 形式展示，由用户手动插到正确层级（盲 append 会破坏 YAML 结构）。绝不覆盖已有值。
6. **兼容 dry-run**：跑 `python3 .claude/skills/worklog-lint/scripts/lint.py` 验证契约锚点仍匹配；🔴 则输出手动调整清单。
7. **收尾**：commit（`chore: skill 升级至 <tag>`）+ 清理临时目录 + 报告（升级了什么 / 跳过了什么 / settings diff 提示 / 需要手动做的）。

## 边界

- 网络失败 / tag 不存在 → 报告后干净退出，不留半套状态（临时目录必删）。
- 上游 skill 被移除时不自动删本地对应目录，只提示（删除是用户决定）。
