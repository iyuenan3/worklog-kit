---
name: worklog-query
description: 跨日记与 wiki 检索。用户说「查 X / X 项目最近怎么样 / 上周干了什么 / 那个决策为什么」时触发：按意图分流（项目 / 时间段 / 关键词 / 决策溯源），综合 wiki 项目页与关联日记给出带出处的答案。只读不写。
---

# worklog-query：查 X

> 与用户交互的语言跟随其消息语言。**只读**：本 skill 不修改任何文件。

## 检索通道：Obsidian CLI 优先（可选加速）

关键词 / 标签 / 链接类检索先试官方 `obsidian` CLI（Obsidian app 内置，需 app 在运行）。**只用查询型命令**（read / search / tags / links / files 等，纯返回数据）；open / daily 这类会把 app 弹到前台，不用。

1. **探测**：`command -v obsidian` 存在 → 试跑一条只读命令（如 `obsidian files`），成功且输出确认是本 vault 的文件即可用
2. **拉起**：探测失败、系统是 macOS 且装有 Obsidian → `open -ga Obsidian`（后台启动，不抢焦点），等约 3 秒重试一次探测；用了这条就在最终回答末尾提一句「已后台启动 Obsidian」
3. **回退**：仍不可用（未装 / 无 GUI / 本 vault 未在 Obsidian 打开注册过）→ 静默走下表 rg / grep 路径，不报错、不追问、本次不再重试

CLI 只是加速通道：回答口径不变（结论带出处），CLI 结果与文件实读不一致时以文件为准。

## 意图分流与检索路径

| 问法 | 路径 |
|---|---|
| 查某项目（「X 最近怎么样」） | 先读 `wiki/projects/<slug>.md`（现状 + 决策日志），再按其 frontmatter `diaries` 数组回读最近几篇相关日记的对应章节 |
| 查时间段（「上周干了什么」） | 按 config 时区换算日期范围（先 `export TZ=<config.timezone>`），逐读 `diaries/<D>.md` 的概览与主线，汇总 |
| 查关键词（「关于 Y 的记录」） | 先走 Obsidian 通道（`obsidian search` 等，见上节）；不可用则 `rg -n --glob '!**/.git/**' '<关键词>' diaries/ wiki/ inbox/`（无 rg 退 `grep -rn`；中文字面量加 `LC_ALL=C`）；命中多时按时间倒序取最相关的深读 |
| 决策溯源（「当初为什么这么定」） | 项目页决策日志 → 对应日期日记的项目章节 → `AIREADME/DECISIONS.md`，三处交叉 |

## 回答要求

- **每个结论带出处**：`文件:行` 或日记日期，让用户可跳转核实
- 检索为空就说没查到 + 给出试过的路径，不编造
- 涉及日期与星期的表述先工具换算，不心算
