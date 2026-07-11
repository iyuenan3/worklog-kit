#!/usr/bin/env bash
# 飞书连接器认证自检。退出码: 0 可用 / 1 未认证 / 2 未装 lark-cli。
# lark-cli 是 node CLI，非交互 shell 的 PATH 注入常在 rc 里缺席 → 统一经 bash -lc 调用（见 pitfalls「非交互 SSH 不加载 rc」条）。
set -uo pipefail
if ! bash -lc 'command -v lark-cli' >/dev/null 2>&1; then
  echo "lark-cli not installed: npm i -g @larksuite/cli (then run feishu-setup)"
  exit 2
fi
# fetch.sh 解析消息硬依赖 python3：这里不查，check 会假绿、到 fetch 才失败
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found (fetch.sh needs it to parse messages)"
  exit 2
fi
# 带超时的认证探测（钥匙串锁定 / 网络问题都可能让它挂住；无 timeout 用 perl alarm，皆无才裸跑）
if command -v timeout >/dev/null 2>&1; then _t() { timeout 20 "$@"; }
elif command -v perl >/dev/null 2>&1; then _t() { perl -e 'alarm shift; exec @ARGV' 20 "$@"; }
else _t() { "$@"; }
fi
if _t bash -lc 'lark-cli auth status' >/dev/null 2>&1; then
  echo "ok"
  exit 0
fi
echo "not authenticated: run 'bash -lc \"lark-cli auth login\"' (token expires roughly weekly)"
exit 1
