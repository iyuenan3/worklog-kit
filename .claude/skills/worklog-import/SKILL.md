---
name: worklog-import
description: 素材摄入。用户丢来文件（PDF / Word / PPT / Excel / HTML / CSV / EPUB）说「收进 inbox / 转成 markdown / 导入这个」，或 worklog-init 存量迁移批量调用时触发：经 markitdown 转成 markdown 落入 inbox/，附 provenance frontmatter，供当晚 ingest 引用与后续消化。
---

# worklog-import：素材摄入

> `inbox/` 是 vault 的原料收件箱：人放、AI 消化。本 skill 只负责「放得规范」，消化归 ingest 与用户。与用户交互的语言跟随其消息语言。

## 前置

```bash
command -v uvx || command -v uv    # 缺 → 给安装命令（brew install uv 或官方 curl 脚本），装完继续
```

## 单文件模式（日常）

1. 转换：`uvx markitdown '<源文件>' > '<临时输出>'`（图片 LLM 描述保持默认关闭，不外发任何内容）
2. 落盘：`inbox/<YYYY-MM-DD>-<原文件名 slug>.md`（日期按 config 时区的今天；同名已存在则加序号，绝不覆盖）
3. 头部插 provenance frontmatter：

```yaml
---
source: <原文件名>
imported: <YYYY-MM-DD HH:MM>
tool: markitdown
---
```

4. **质量自检**：转出内容近空或全是乱码（常见于扫描版 PDF，需 OCR，超出 v0.1 范围）→ 照样落盘但 frontmatter 加 `quality: poor-needs-ocr`，并明确告诉用户
5. 报告：落盘路径 + 一句内容概要 + 提醒「当晚 ingest 会引用今日新增，深度消化说一声即可」

## 批量模式（init 存量迁移调用，或用户指一个目录）

1. 先盘点不动手：遍历目录列出可转文件（docx / pptx / xlsx / pdf / html / csv / epub），报数量与总大小
2. **超过 50 个文件或单文件超过 10MB → 先给清单与耗时预估，确认后再跑**（批量属交互场景，可以问）
3. 逐个按单文件模式转换；单个失败记入清单继续，最后汇总（成功 N / 失败 M / 需 OCR K）

## 边界

- 不自动消化进 wiki（那是 ingest 与用户的事）；不主动 commit（用户或当晚 ingest 顺带提交）
- 源文件不移动不删除（用户的原件用户管）
- 任何转换都在本地完成，内容不经网络外发
