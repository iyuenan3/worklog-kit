# 操作日志

> append-only：每次 ingest 在锚点下方追加一段 `## [YYYY-MM-DD] ingest`。累积超过一年时按 `log-YYYY.md` 轮转归档（防大文件读取截断）。

<!-- ingest:log-anchor（新条目插在本行之下，勿删） -->
