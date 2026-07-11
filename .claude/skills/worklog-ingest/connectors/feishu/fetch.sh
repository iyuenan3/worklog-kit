#!/usr/bin/env bash
# 飞书 fetch：拉窗口内指定会话的消息，输出 IM digest 行协议（见 ../README.md）。
# 用法: bash fetch.sh --since <ISO8601> --until <ISO8601> --chats 'oc_xxx[,oc_yyy]' --me <open_id 或姓名> [--record-others]
#   --me 必填（区分本人消息的唯一依据，精确匹配 sender id 或姓名；feishu-setup 引导优先用 open_id）
#
# 行协议注意（消费方）:
#   - MSG 的 | 分隔固定 4 段；author 与 text 内原生 | 已被替换为 ¦，可安全按 | 全拆
#   - NOTE 走 stdout（协议流的一部分）；调试详情另有一份在 stderr
# 实现注记（lark-cli v1.0.x 实测命令面）:
#   - stdout 可能混入 JSON 之外的 warning 行 → 只认合法 JSON 行
#   - 消息正文常是 JSON 字符串（{"text": ...}）→ 二次解析兜底
#   - 超时用「后台执行 + watchdog kill」：$() 直接包 perl alarm 会因子进程持有管道 fd 而失效（实测复现）
#   - 参数经 bash -lc 'exec "$@"' 传递，不做字符串拼接（防引号断裂）
# 降级契约: 单会话失败输出 NOTE 继续下一个，整体以非零退出标示局部失败；绝不交互、绝不无限阻塞。
set -uo pipefail
export LC_ALL=C

SINCE="" UNTIL="" CHATS="" ME="" OTHERS=0
while [ $# -gt 0 ]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --until) UNTIL="$2"; shift 2 ;;
    --chats) CHATS="$2"; shift 2 ;;
    --me) ME="$2"; shift 2 ;;
    --record-others) OTHERS=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
[ -n "$SINCE" ] && [ -n "$UNTIL" ] && [ -n "$CHATS" ] && [ -n "$ME" ] || {
  echo "Usage: bash fetch.sh --since <ISO> --until <ISO> --chats 'oc_xxx[,...]' --me <open_id|name> [--record-others]" >&2
  exit 2
}

bash -lc 'command -v lark-cli' >/dev/null 2>&1 || { echo "lark-cli not installed" >&2; exit 2; }

TMO="${WORKLOG_IM_TIMEOUT:-45}"

# 超时安全调用：后台跑 + watchdog 杀；输出落临时文件避免管道 fd 悬挂
fetch_chat_raw() {  # $1=chat_id  $2=输出文件；返回 lark-cli 退出码（被杀视为失败）
  ( bash -lc 'exec "$@"' _ lark-cli im +chat-messages-list \
      --chat-id "$1" --start "$SINCE" --end "$UNTIL" \
      --order asc --page-size 50 --no-reactions --format ndjson >"$2" 2>/dev/null ) &
  pid=$!
  ( sleep "$TMO"; kill "$pid" 2>/dev/null ) &
  wd=$!
  wait "$pid" 2>/dev/null
  rc=$?
  kill "$wd" 2>/dev/null; wait "$wd" 2>/dev/null
  return "$rc"
}

process_chat() {  # $1=chat_id
  chat="$1"
  printf 'CHAT %s\n' "$chat"
  tmpf=$(mktemp "${TMPDIR:-/tmp}/worklog-feishu.XXXXXX") || return 1
  if ! fetch_chat_raw "$chat" "$tmpf"; then
    printf 'NOTE chat %s: fetch failed or timed out\n' "$chat"
    echo "chat $chat: fetch failed/timeout (auth expired? run: bash -lc 'lark-cli auth login')" >&2
    rm -f "$tmpf"
    return 1
  fi
  if [ ! -s "$tmpf" ]; then
    printf 'NOTE chat %s: empty response (quiet chat, left chat, or missing permission)\n' "$chat"
    rm -f "$tmpf"
    return 0
  fi
  # 解析、方向判定（精确匹配）、过滤、| 消毒全部在 python 内完成，bash 不再做字段级字符串操作
  # 数据经 argv 传文件路径：python3 - 的程序体已占用 stdin（heredoc），不能再用 stdin 传数据
  python3 - "$ME" "$OTHERS" "$tmpf" <<'PYEOF'
import sys, json
me, others = sys.argv[1], sys.argv[2] == "1"
saw_json = False
for line in open(sys.argv[3], encoding="utf-8", errors="replace"):
    line = line.strip()
    if not line.startswith("{"):
        continue                                    # 挡 warning / 非 JSON 行
    try:
        m = json.loads(line)
    except Exception:
        continue
    saw_json = True
    ts = m.get("create_time") or m.get("createTime") or ""
    if not ts:
        continue                                    # 无时间戳的消息丢弃，防字段左移产出畸形行
    sender = m.get("sender") or {}
    sid = str(sender.get("id") or sender.get("sender_id") or m.get("sender_id") or "")
    sname = str(sender.get("name") or m.get("sender_name") or sid or "unknown")
    body = m.get("body") or {}
    content = (body.get("content") if isinstance(body, dict) else None) or m.get("content") or ""
    try:
        c = json.loads(content)
        text = c.get("text") or c.get("title") or json.dumps(c, ensure_ascii=False)[:120]
    except Exception:
        text = str(content)
    text = " ".join(str(text).split())[:200]
    if not text:
        continue
    out = (sid == me) or (sname == me)              # 精确匹配：防前缀 / 子串把他人误标为本人
    if out or others:
        safe_name = sname.replace("|", "¦")
        safe_text = text.replace("|", "¦")
        print("MSG %s|%s|%s|%s" % (str(ts).replace("|", "¦"), "out" if out else "in", safe_name, safe_text))
if not saw_json:
    print("NOTE message structure unrecognized, calibrate fetch.sh against actual lark-cli output")
PYEOF
  rm -f "$tmpf"
  return 0
}

printf 'PROVIDER feishu\n'
fail=0
# chat id（oc_ 开头）不含空格，按逗号转空格后 for 分词安全，且避开在循环里反复改 IFS 的脆弱模式
for chat in $(printf '%s' "$CHATS" | tr ',' ' '); do
  [ -n "$chat" ] || continue
  process_chat "$chat" || fail=1
done
exit "$fail"
