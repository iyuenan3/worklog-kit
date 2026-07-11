# IM 连接器接口（v1）

IM 是最因人而异的数据源，必须连接器化。每个连接器 = 本目录下 `<provider>/`，两个可执行入口：

## 1. `check.sh` 认证自检

无参数。退出码：`0` 可用 / `1` 未认证 / `2` 未安装。stdout 一行状态说明（未认证 / 未装时附修复命令）。ingest 与 setup skill 都靠它分流。

## 2. `fetch.sh` 拉取窗口消息

```
bash fetch.sh --since <ISO8601> --until <ISO8601> --chats '<id1>[,<id2>...]' --me <本人标识> [--record-others]
```

`--me` 必填（区分本人消息的唯一依据，**精确匹配** sender id 或姓名；优先用 open_id，全局唯一不会碰撞）。

输出 digest 行协议（stdout）：

```
PROVIDER <name>
CHAT <会话名或 id>
MSG <iso-time>|<out|in>|<author>|<单行文本摘要>
NOTE <description>             （单会话失败 / 空响应 / 结构未识别等，属协议流的一部分，走 stdout）
```

MSG 固定 4 段：`author` 与 `text` 内原生 `|` 由连接器替换为 `¦`，消费方可安全按 `|` 全拆。

**分页边界**：底层 CLI / API 单次拉取可能截断时，连接器必须在命中上限时输出 NOTE 提示（消费方转进晨报）；实现了完整翻页的连接器可免。参考实现 feishu 单页上限 50 条、无自动翻页，命中即 NOTE。

## 契约（所有连接器必须遵守）

- **隐私在采集层执行**：默认只输出 `out`（本人发出）的 MSG，他人内容根本不进 digest；`--record-others` 才含 `in`，该开关只由 config `record_others` 驱动
- **降级**：任何失败（未认证 / token 过期 / 网络 / 企业限制）→ 非零退出 + stderr 一行原因；**绝不交互、绝不无限阻塞**（内部自带超时）；单会话失败继续下一个
- **零日期运算**：窗口由调用方按 config 时区算好传入

## IM 数据使用须知（合规责任在用户）

启用 IM 源前自行评估三件事：① 被记录的同事并不知情，默认只记你自己发出的消息就是为此设计的底线，开 `record_others` 前请确认合规；② 企业 IM 内容可能受雇主信息安全政策约束，摘录进个人 vault 是否允许由你判断；③ 私有 GitHub 仓不等于绝对安全，push 上去的数据仍在第三方服务器上。

## ingest 消费纪律（digest → 日记）

- MSG 只作当日协调工作的素材，按 judgment 汇编成协调段落，不逐条罗列
- **不臆断他人的确认或承诺**（digest 默认只有你自己发的消息，看不到对方回复，别脑补）
- 清单类内容（功能列表、待办清单）逐字照录，不改写

## 已有实现

- [`feishu/`](feishu/)：飞书（官方 `@larksuite/cli`），v0.1 参考实现；安装与认证走 `feishu-setup` skill

新增连接器（slack / 企业微信 / Teams 等）：按上述两脚本 + 契约实现即可，欢迎贡献。
