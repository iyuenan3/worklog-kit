---
name: worklog-lint
description: vault 健康检查。用户说「检查 / lint / 体检」时触发：跑通用机械项（契约锚点 / 凭证扫描 / 断链 / frontmatter / log 轮转阈值），config language 为 zh 时追加标点门与日期门；报告 must-fix 与 advisory，经确认后可代修。
---

# worklog-lint：vault 健康检查

> 与用户交互的语言跟随其消息语言。只检查与报告，修复动作逐项经用户确认（除非用户明说「直接修」）。

## 流程

1. **通用机械项**：

```bash
python3 .claude/skills/worklog-lint/scripts/lint.py
```

🔴 must-fix（exit 1）：契约锚点缺失、疑似凭证、diary frontmatter 缺 date（只查 `YYYY-MM-DD.md` 命名的文件，同步冲突副本等杂件降为 advisory）。🟡 advisory：断链（跨库引用可忽略，判断前先问用户该链接是否指向 vault 外）、项目页 frontmatter 缺字段、log.md / index.md 增长超阈值该轮转归档、diaries/ 里的非日记命名文件。凭证扫描的有意示例行可加行内 `lint:ignore` 标记豁免（仅正文区生效，config 不豁免）。

2. **zh 写作门**（config `language: zh` 才跑；复用 ingest 随包脚本，脚本不存在则提示「worklog-ingest 未安装或版本过旧，跳过写作门」不报错）：

```bash
python3 .claude/skills/worklog-ingest/scripts/punctuation_check.py <改动过的 md 或用户点名的文件>
python3 .claude/skills/worklog-ingest/scripts/date_weekday_check.py --all
```

3. **报告**：按 🔴 / 🟡 分组列出，每条附一句「怎么修」；🔴 建议当场修（凭证类必须当场处理并提醒若已 push 需轮换该凭证），🟡 尊重用户节奏。
4. **修复**（经确认）：逐项修，修完重跑对应检查验证归零。

## 边界

- 凭证命中即最高优先级：先处理再谈别的；已入 git 历史的凭证提醒「删除文件不够，需轮换凭证本身」。
- 断链不自动删改（可能是用户有意的跨库引用）；log 轮转属结构操作，给命令让用户跑或经确认代跑。
