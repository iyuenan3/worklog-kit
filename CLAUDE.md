# CLAUDE.md · 我的 worklog（router）

> 本仓 = 你的「父项目」vault：三层架构（日记只追加 / wiki 由 LLM 维护 / schema 人 + LLM 共演）的个人知识库 + 工作日记系统，由 [worklog-kit](https://github.com/iyuenan3/worklog-kit) 驱动。
> 配置在 `worklog.config.yaml`（凭证只放 `worklog.config.local.yaml`，不入 git）。方法论全文见 `docs/methodology.md`。

## 路由（触发语 → 行为）

| 触发 / 任务 | 行为 | skill |
|---|---|---|
| 「初始化 / init」 | 初始化 vault：预检 + config 生成 + 项目定级 + 全局 skill 安装 | worklog-init |
| 「记录今天 / 昨天 / YYYY-MM-DD / 补充今天 / 更新日记 / 回填 N 天」 | 无人值守 ingest：扫描各数据源编译日记 + 更新 wiki + TODO 盘点 + commit | worklog-ingest |
| 丢文件进来 / 「收进 inbox」 | 素材转 markdown 入 `inbox/` | worklog-import（即将推出） |
| 「查 X」 | 跨日记 + wiki 检索 | worklog-query（即将推出） |
| 「检查 / lint」 | 断链 / frontmatter / 凭证扫描 | worklog-lint（即将推出） |
| 「升级 skill」 | 从 upstream 拉 skill 新版（只动 `.claude/skills/`，永不碰你的数据） | worklog-update（即将推出） |

> 日期边界：00:00 至 config `day_boundary`（默认 07:00）算前一天。时区按 config `timezone`。

## 红线

- **三层所有权**：`diaries/` 只追加、绝不覆盖历史；`wiki/` 由 ingest 维护，手改请保留段落锚点（index 三段标题 / log 锚点注释 / todos 分区标题）；schema 演化记进 `AIREADME/`（决策理由进 DECISIONS）。
- **隐私**：本仓必须保持**私有**（ingest push 前自动检测 visibility）；凭证 / 私钥绝不入 git（.gitignore 已预置兜底）；IM 源默认只记你自己发的消息。
- `inbox/` 是原料收件箱：人放、AI 消化，消化完可归档删除。

## 维护

- 结构演化是这套系统的设计预期：除上面锚点与契约文件外，一切按你的用法长；变了就用 `/aireadme` 更新 `AIREADME/`。
- 新项目 / 新设备 / 新 IM：在 `worklog.config.yaml` 的 `sources` 加一条即可，级别不确定就先 `presence`。

---
> 开发 worklog-kit 本体（而非使用本 vault）？读 `docs/dev/`。作为 vault 用户可忽略本行（init 移除 dev 文档时会一并清理）。
