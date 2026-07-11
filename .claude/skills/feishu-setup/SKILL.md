---
name: feishu-setup
description: 飞书 IM 连接器的安装与认证向导。用户说「配置飞书 / 接入飞书 / feishu setup」或 worklog-init 数据源问答选了飞书时触发：安装官方 lark-cli、应用凭证与授权、macOS 无人值守适配、发现会话 id、写入 config、自检试拉。交互式（这是配置环节，可以提问）。
---

# feishu-setup：飞书连接器接入向导

> 目标：让 `connectors/feishu/`（check.sh + fetch.sh）在你的机器上深夜无人值守可用。全程交互，逐步确认；与用户交互的语言跟随其消息语言。

## Step 1 · 安装 lark-cli

```bash
npm i -g @larksuite/cli && bash -lc 'lark-cli --version'
```

无 npm → 先装 Node（brew / nvm / 官网任一）。**此后一切 lark-cli 调用都经 `bash -lc`**（node 的 PATH 注入常在交互 rc 里，非交互环境会找不到命令）。

## Step 2 · 应用凭证与授权

1. `lark-cli config init` 需要一个飞书应用的 app-id / app-secret：个人租户可在飞书开放平台建自建应用（开通 im 读取等所需 scope）；**企业租户受管时可能不允许自建应用或不给 scope，这一步卡住 = 你的企业不支持本连接器**，此时在 `worklog.config.yaml` 里删掉或注释 feishu 源即可，ingest 其余一切照常（不影响主流程）
2. `lark-cli auth login`（Device Flow 扫码授权）
3. 验证：`lark-cli auth status`；scope 不足时用 `lark-cli auth scopes` 对照

## Step 3 · macOS 无人值守适配

macOS 上 lark-cli 默认把凭证放系统钥匙串，深夜的非交互会话可能读不到（钥匙串锁定 / 无 UI 授权）。执行：

```bash
bash -lc 'lark-cli config keychain-downgrade'
```

把凭证存储降级为本地文件。**权衡要向用户说明**：文件模式少了钥匙串保护，凭证明文落盘在 lark-cli 配置目录（本就不在 vault 内、不会入 git），接受才做；不接受则飞书源只能在交互会话里跑。

## Step 4 · 发现要拉的会话

```bash
bash -lc 'lark-cli im +chat-search --query "<群名关键词>"'   # 按名字找群，拿 oc_ 开头的 chat_id
bash -lc 'lark-cli im +chat-list --types=p2p,group'          # 或列全部会话挑选
```

引导用户挑选与工作协调相关的少数会话（宁少勿多：这是「会被读取」的范围，同意机制与项目定级同理）。同时确认「本人标识」`me`：**优先用 open_id**（`lark-cli auth status` 可见；全局唯一，fetch.sh 做精确匹配不会碰撞），姓名仅在拿不到 open_id 时兜底（同名同事会导致误判归属）。

## Step 5 · 写入 config

在 `worklog.config.yaml` 的 `sources` 写入（或更新）：

```yaml
- {type: im, provider: feishu, via: lark-cli, chats: ["oc_xxx", "oc_yyy"], me: "<open_id 或姓名>", on_unreachable: note, record_others: false}
```

`record_others` 默认 false（只记你自己发的消息）；用户明确要求记录他人时才改 true，并向用户复述 `connectors/README.md`「IM 数据使用须知」的三点合规责任。

## Step 6 · 自检与试拉

```bash
bash .claude/skills/worklog-ingest/connectors/feishu/check.sh
bash .claude/skills/worklog-ingest/connectors/feishu/fetch.sh --since '<今天 00:00 带时区>' --until '<现在>' --chats '<oc_xxx>' --me '<标识>'
```

- check 通过 + fetch 有 MSG 输出 → 完成，报告「今晚 ingest 起飞书源生效」
- fetch 输出 `NOTE 消息结构未识别` → lark-cli 版本的输出结构与解析器有偏差，把一条真实输出样本（脱敏）贴给维护者或自行校准 fetch.sh 的字段映射
- 任何一步卡在企业权限 → 回 Step 2 的优雅退出路径

## 已知坑速查（随版本可能变化，用前自测）

- 非交互环境找不到 lark-cli → 一律 `bash -lc`
- token 约周级过期 → ingest 会降级并在晨报提示 `lark-cli auth login`，属常态不是故障
- stdout 可能混入 JSON 之外的 warning 行 → fetch.sh 已按行过滤，自己手工解析时注意
- 消息正文是 JSON 字符串（`{"text": ...}`）→ 要二次解析
