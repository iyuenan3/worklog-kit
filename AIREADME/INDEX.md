# 我的 worklog · AIREADME
> 个人父项目 vault：日记 + wiki + 项目生命周期中枢 ｜ 生命周期: active
> last-synced: f0fa3ab · 2026-07-13
<!-- 同步锚点：初始化后由 aireadme skill 维护，格式 `<SHA> · YYYY-MM-DD`。 -->

## 状态
| 文件 | 状态 | 摘要 |
|---|:--:|---|
| CORE | ✅ | vault 身份与红线 |
| RELATIONS | ✅ | 上游 worklog-kit + 子项目关系 |
| ARCHITECTURE | ✅ | 三层架构 + 数据流 + 多仓/非 git 采集 + 禁改项 |
| CONVENTIONS | ✅ | 日记 / 项目页最小契约（含 path: 锚点、子树否决） |
| SPEC | — | N/A 无对外接口 |
| DEPLOYMENT | — | N/A 本地 + git 私仓 |
| PRD | — | N/A → CORE |
| ROADMAP | ⚑ | 待你的第一批计划 |
| DECISIONS | ✅ | append-only；D1 多仓独立成项 / D2 path: 消歧锚点 |
| MEMORY | ⚑ | append-only，随踩坑记录 |
| CHANGELOG | ✅ | append-only；kit 发布史与 vault 版本单一流（至 v0.7） |

## 按任务读
- 了解这个 vault → CORE + ARCHITECTURE
- 改 wiki 结构 / schema → CONVENTIONS + DECISIONS（记理由）
- 多仓 / 非 git 项目怎么采集 → ARCHITECTURE「本机项目采集」+ DECISIONS D1/D2
- 子项目关系 → RELATIONS
