# worklog-kit 开发路由（dev-only，随 init 移除）

> 仓根即模板：根目录一切文件是**产品件**（用户 vault 的一部分），开发文档只住本目录。

- 需求 / 规格真相源：[`PRD.md`](PRD.md)（含冻结契约 §5、ingest 重写规格 §8、修订记录）
- 深度 review 方法论：[`deep-review.md`](deep-review.md)（开发工序笔记，明确不产品化）
- 方法论：[`../methodology.md`](../methodology.md)（产品件，随模板分发）
- 版本史：[`../../AIREADME/CHANGELOG.md`](../../AIREADME/CHANGELOG.md)（kit 发布史与 vault 版本单一流，2026-07-12 起）
- 里程碑：PRD §15（M1 模板骨架 → M2 ingest 重写 → M3 连接器 → M4 收尾 → M5 pilot 与发布）

## 开发红线

- **本仓已公开（2026-07-12 起 public + template），一切内容即时对外可见**（含 commit message 与 git 全历史）：不得含维护者个人信息、客户 / 雇主名、具名设备、IM 群坐标、真实同事称呼；每次 push 前自查 diff 与 commit message。
- **禁止随意改写已 push 的历史**：外部用户可能已 clone，任何 force push 前先停下评估影响并说明。
- **通用性红线**（PRD 原则 2）：核心流程零特定 IM / 平台 / 语言 / 公司环境假设；评审任何改动先问「一个用 Slack、说英文、不在中国的陌生用户拿到后还能用吗」。
- 冻结契约（PRD §5）改动必须同步 PRD，并评估对已铺出去的用户 vault 的兼容性。
- 三件套（aireadme / stash / pitfalls）canonical 在本仓维护（personal-skills 侧指针于 kit 公开时落地），修改直接在本仓做。
- 中文文案用中文全角标点，绝不使用破折号。

## 惯例

- git 直接提 `main`；发布走 release tag（worklog-update 的拉取单位）。tag 格式 = semver `vX.Y.Z`；打 tag 时把 `AIREADME/CHANGELOG.md` 对应 Unreleased 段改为「vX.Y.Z（日期）」，两者一一对应。
- 借鉴维护者私有实现时只搬骨架不搬数据，任何本机路径不得写进产品件。
