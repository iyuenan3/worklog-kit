---
name: worklog-maintain
description: vault 记忆维护（批处理 GC + 碎片整理）。用户说「维护 vault / vault 保养 / 处理体检项 / maintain vault」或循日记体检提醒行而来时触发：现场重跑 lint --health 体检，按腐坏类型分批修复（状态漂移 / 孤儿页 / 实体分裂 / 膨胀 / TODO 年龄），每类一个 commit，修完全门验收出小结。交互触发才动文件；定时 / 无人值守触发只出报告。
---

# worklog-maintain：vault 记忆维护

> ingest 是增量编译器，只看见当晚窗口；本 skill 是批处理维护工序（GC + 碎片整理），处理跨月才显形的腐坏。与用户交互语言跟随其消息语言，写入 vault 的内容按 config `language`。

## 授权模型（跟触发方式走，无全局开关）

- **交互触发**（用户此刻发的消息，含「处理体检项」）= 明示授权：wiki / todos 类修复直接做，git 可回滚，无需逐项确认。
- **定时 / 无人值守触发**（schedule / cron / headless 会话），或用户明说「报告模式」= 只跑体检出报告，**不动任何文件**。判不准当无人值守处理（宁可少动）。

## 红线

1. `diaries/` **永不触碰**：历史日记只读，连标点都不改（它是全系统的事实源）。
2. wiki 只做**合并 / 归档 / 重链**，删除留给人：归档 = `git mv` 进 `wiki/archive/`；合并后旧名留 alias 存根（见修复配方），绝不让历史日记里的 wikilink 变幽灵。
3. TODO 僵尸**只标记不关闭**（出厂默认）：加 `#todo/stale` 与一句标注；打勾或删除是用户的决定。

## 原则

证据先行（不信旧报告与日记提醒行的数字，现场重跑体检）；每次只处理**体检列出的明确问题**（清单之外的「顺手优化」不做）；不为整洁删除仍有价值的内容（价值拿不准 → 归档而非删除，或留给用户并说明）。

## 流程

### 1. 现场体检

```bash
python3 .claude/skills/worklog-lint/scripts/lint.py --health
```

- `🩺 0 项待维护` → 报告「vault 健康，无需维护」，结束。
- 有待维护项 → 逐项列给用户看。无人值守模式到此为止（报告即产出）；交互模式继续。

### 2. 按腐坏类型分批修复（每类修完立即一个 commit）

| 体检项 | 修复配方 |
|---|---|
| 状态漂移 | 读该项目页 + 最近提及它的几篇日记，把项目页现状与决策日志补到与日记一致，刷新 `last_updated`；页与日记冲突以日记为准（日记是事实源） |
| 孤儿页 | 先判断价值：仍有价值 → 从相关 wiki 页补一条入链；已完结 / 过时 → `git mv` 入 `wiki/archive/`（不删除）；拿不准 → 不动，小结里列出留给用户 |
| 实体分裂 | 选 canonical 名（优先已有项目页的名字），把 wiki 与 todos 里的变体 wikilink 全部重链到 canonical（**diaries 一个都不改**）；变体若自有页面，内容并入 canonical 后原页改为 alias 存根：frontmatter 写 `alias_of: <canonical>` + 正文一行指针（存根让历史日记链接仍可解析，体检也不再把它算分裂）；候选是机械归一化产物，中英别名等语义级同一性由你判断，误报直接跳过并在小结说明 |
| 膨胀 | 页面超体积 → 历史段落移入 `wiki/archive/<页名>-<年份>.md`，原页留一行指针；决策日志超条数 → 老条目移入 `wiki/archive/<slug>-decisions.md`，原段保留最近条目 + 一行指针 |
| TODO 年龄 | 逐条对照日记与项目页：确认已完成的打勾 + 补完成日期；仍有效的不动；僵尸（长期无进展无提及）加 `#todo/stale` + 一句标注，不关闭（已标记的任务体检不再重复报，等用户处置） |

commit：每类一个，格式 `maintain: <类型>（<N> 项）`（en vault 用 `maintain: <type> (<N> items)`），正文列触及文件；尾行 Co-Authored-By 约定与 ingest D.4 相同。

### 3. 验收 + 收尾

1. 重跑 `lint.py`（正误节必须 0 must-fix）+ `lint.py --health`（目标归零；因「留给用户」未归零的逐条说明）
2. 写作门：对本次改动的 md 跑标点门（仅 zh）与日期门（与 ingest D.4 同规）
3. push 一次：前置 visibility 检测（与 ingest D.4 同规）；检测不可用则跳过检测照常 push
4. **维护小结**：每类修了几项 / 归档了什么 / 留给用户什么及原因 / 阈值是否建议调整（只建议，不代改 config）。维护记录不做额外记账：maintain commit 由当晚 ingest 的 vault 内部源自然收录进日记。

## 边界

- v1 管辖仅 vault 仓内：`wiki/`（含 `wiki/archive/`）与 `wiki/todos.md`；`diaries/` 只读。不碰 `~/.claude` 下的 memory（git 之外不可回滚，瘦身走 `docs/maintenance.md` 手工配方）、不碰两层 config、不碰 `.claude/skills/`。
- 阈值不合口味是 config 问题不是维护问题：提示用户改 `worklog.config.yaml` 的 `maintenance:` 段。
- 体检脚本缺失（worklog-lint 未装或版本过旧）→ 明确报告后结束，不徒手模拟体检。
