---
name: worklog-export
description: 数据导出（退出通道）。用户说「导出 / 迁走 / export」时触发：把 diaries 与 wiki 转成不依赖任何工具链的纯 markdown 落到 export/ 目录。vault 数据本就属于用户，本 skill 保证「离开时带得走」。
---

# worklog-export：退出通道

> 与用户交互的语言跟随其消息语言。**只读源文件**，产物写进 `export/<YYYY-MM-DD>/`（该目录建议用户导出后自行移走，不必入 git）。

## 转换规则

1. 目录结构原样复制 `diaries/` 与 `wiki/`（inbox 原料与 config 询问是否需要）
2. **wikilink 去方言**：`[[页名|别名]]` → `别名`；`[[页名]]` → 目标存在时改相对 markdown 链接 `[页名](相对路径.md)`，不存在则退纯文本 `页名`
3. **Obsidian Tasks 查询块**：` ```tasks ... ``` ` 代码块整块移除（那是查询视图不是数据；任务行本身 `- [ ] ...` 是标准 markdown，原样保留）
4. **任务行尾的 Tasks 元数据 emoji**（📅 / ✅ / ⏳ / 🔁 等 + 日期）默认一并去除（非 Obsidian 下是视觉噪音）；用户要保留就保留（导出前问一句）
5. frontmatter 保留（标准 YAML，任何工具可读或忽略）
6. 用 python 脚本化执行以上替换（正则处理 CJK 时注意编码，逐文件 UTF-8 读写），不逐文件手改

## 收尾报告

- 导出文件数、落地路径、转换统计（改写了多少 wikilink、移除了多少查询块）
- 提醒：项目记忆（Claude Code memory 目录）在 `~/.claude/projects/` 下，属 vault 外资产，需要的话手动复制
