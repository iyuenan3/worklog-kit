# CONTRIBUTING

本项目由维护者业余时间维护：bug 直接开 issue（用模板，只贴脱敏输出），PR 欢迎但不保证合并速度。

## 改动必须遵守的三条红线

1. **通用性**：核心流程不得引入特定 IM / 平台 / 语言 / 公司环境假设；特定能力下沉为连接器（`connectors/README.md` 接口）或 locale 模板。自查一句话：一个用 Slack、说英文、不在中国的用户拿到后还能用吗。
2. **无人值守**：ingest 链路上的任何改动不得引入「等用户回答」或可能无限阻塞的调用（外部调用必须带超时）；失败一律降级记录。
3. **隐私**：不引入遥测；IM 数据过滤必须在采集层；示例与文档不得含任何真实个人 / 公司信息。

## 提交前

- `bash -n` 过所有改动的 .sh；`python3 -m pytest tests/`；改了中文文档跑 `python3 .claude/skills/worklog-ingest/scripts/punctuation_check.py <文件>`（中文全角标点，不用破折号）
- 冻结契约（`docs/dev/PRD.md` §5）相关的改动必须同步 PRD 并说明对存量用户 vault 的兼容性

## 贡献新 IM 连接器

按 `connectors/README.md` 的接口 v1 实现 `check.sh` + `fetch.sh`，随 PR 附 fixture 级测试说明（真实租户凭证不进仓）。
