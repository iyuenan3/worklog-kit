# TODO

> 主存储：活跃待办记在下方 `## 进行中` / `## 待办` 分区，Obsidian Tasks 语法。非 Obsidian 环境下 `tasks` 代码块显示为普通文本，不影响记录本身。
> 语法：`- [ ] 描述 #todo/<类型> [[关联页]] 📅 YYYY-MM-DD`（每条真 TODO 必带 `#todo/<类型>` 标签，聚合视图靠它正向收口）。
> 文件只负责存储；「当前有哪些待办」的视图不写死在这里，问 Claude 现算现给（ingest 收尾也会打一份本次未完成清单）。
> ingest 每次盘点：读 git log 与项目记忆核对进度后判 4 态（完成打勾 + 证据、失效划掉、可拆、顺延），完成项扫入下方归档段，显著停滞标 `#todo/stale`。

## 进行中

## 待办

## 📦 已完成归档

> ingest 把上方主存储本次标 ✅ / ❌ 的完成项扫到此，只留一句结论 + 日期（完整过程见当天日记）。

## 聚合视图（可选，需 Obsidian Tasks 插件）

```tasks
not done
tags include #todo
tags do not include #todo/stale
path does not include diaries/
sort by due
```
