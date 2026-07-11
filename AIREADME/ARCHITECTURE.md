# ARCHITECTURE

## 三层

| 层 | 目录 | 所有权 |
|---|---|---|
| 日记 | `diaries/` | 只追加（ingest 写，人可读可补充） |
| 知识 | `wiki/` | LLM 维护（ingest 更新；人可改，保留锚点） |
| schema | `AIREADME/` + `worklog.config.yaml` | 人 + LLM 共同演化 |

## 数据流

sources（config 声明：本机多 root / 托管平台 / 远程机 / IM / brain-dump）→ 每晚 ingest → `diaries/YYYY-MM-DD.md` + wiki 三处刷新（index 摘要与两表 / log 追加 / 项目页）+ TODO 盘点 → commit + push（push 前 visibility 检测）。

`inbox/` ← 人放原料（worklog-import 转 markdown）→ ingest 引用当天新增，消化进 wiki 后可归档。

## 禁改项
- `wiki/index.md` 三段标题、`wiki/log.md` 锚点注释、`wiki/todos.md` 分区标题（ingest 写入锚点；改了会触发 append 兜底并在晨报警告）
- `worklog.config.yaml` 的 `schema_version` 由 worklog-update 管理，不手改
