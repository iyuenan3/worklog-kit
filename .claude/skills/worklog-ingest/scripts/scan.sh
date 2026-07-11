#!/usr/bin/env bash
# worklog 数据源扫描器：给定时间窗口，扫 roots 下所有 git 仓的当日活动。
# 自足单文件：本地与远程跑同一份（远程 = `ssh host 'bash -s' < scan.sh -- <args>`，不依赖远端 rc / PATH 注入）。
#
# 用法:
#   bash scan.sh --since '<ISO8601>' --until '<ISO8601>' [--authors 'a@x.com,b@y.com,Name'] \
#                [--touch-since 'YYYYMMDDhhmm'] [--depth N] <root> [<root>...]
#
# 时间参数由调用方（Claude 按 config timezone 计算）传入字符串，本脚本零日期运算：
#   --since/--until 原样传给 git log（git 自解析 ISO）；--touch-since 用于 mtime 兜底（touch -t 格式）。
#
# 输出（stdout，行协议，供 LLM 汇编）:
#   REPO <abs-path>                     一个 git 项目开始（含嵌套子仓，各自独立一段）
#   BRANCH <name>                       当前分支
#   COMMIT <short-hash>|<iso-date>|<author>|<subject>    窗口内 commit（--branches --tags，天然排除 refs/stash 伪 commit）
#       ⚠️ 消费方注意：| 分隔只取前三个，第四段 subject 为余部、本身可能含 |
#       ⚠️ --author 为 git 子串匹配（已加 --fixed-strings 关正则），非精确匹配
#       ⚠️ git 的 --until 是闭区间（<=）：调用方要半开窗口 [起, 止) 时，传入的 --until 须自行减 1 秒
#   DIRTY <n>                           未提交变更文件数（无 commit 但有活动的信号）
#   MTIME_ACTIVE                        （仅给了 --touch-since 且窗口内无 commit 时）文件 mtime 有动静
#   IGNORED <abs-path>                  项目根含 .worklogignore（永久 exclude）
# stderr:
#   SKIP_UNMOUNTED <root>               root 不存在（硬盘未挂载等，常态路径）
#   TIMEOUT <path>                      单仓扫描超时（有 GNU timeout 才生效；macOS 无 timeout 则裸跑）
#
# 可移植性（见 pitfalls 库）：BSD/GNU find 通用参数；不用 date -v / find -newermt；bash 3.2 兼容。
set -uo pipefail
export LC_ALL=C

SINCE="" UNTIL="" AUTHORS="" TOUCH_SINCE="" MAXDEPTH=4
while [ $# -gt 0 ]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --until) UNTIL="$2"; shift 2 ;;
    --authors) AUTHORS="$2"; shift 2 ;;
    --touch-since) TOUCH_SINCE="$2"; shift 2 ;;
    --depth) MAXDEPTH="$2"; shift 2 ;;
    --) shift; break ;;
    -*) echo "Unknown option: $1" >&2; exit 2 ;;
    *) break ;;
  esac
done
[ -n "$SINCE" ] && [ -n "$UNTIL" ] && [ $# -ge 1 ] || {
  echo "Usage: bash scan.sh --since <ISO> --until <ISO> [--authors a,b] [--touch-since YYYYMMDDhhmm] <root>..." >&2
  exit 2
}

# identities → 多个 --author（git 语义：多 --author 为 OR）
# 用数组防 word-splitting（作者名可含空格）；bash 3.2 下空数组 + set -u 展开会炸，故展开处用 ${arr[@]+...} 习语
AUTHOR_ARGS=()
if [ -n "$AUTHORS" ]; then
  _old_ifs="$IFS"; IFS=','
  for a in $AUTHORS; do
    a=$(printf '%s' "$a" | sed 's/^ *//; s/ *$//')
    [ -n "$a" ] && AUTHOR_ARGS+=("--author=$a")
  done
  IFS="$_old_ifs"
fi

TIMEOUT_CMD=()
command -v timeout >/dev/null 2>&1 && TIMEOUT_CMD=(timeout "${WORKLOG_SCAN_TIMEOUT:-30}")

# mtime 兜底参照文件（touch -t + find -newer，BSD/GNU 通用；不用 -newermt）
REF_FILE=""
if [ -n "$TOUCH_SINCE" ]; then
  REF_FILE="${TMPDIR:-/tmp}/worklog-scan-ref.$$"
  touch -t "$TOUCH_SINCE" "$REF_FILE" 2>/dev/null || REF_FILE=""
fi

scan_repo() {
  d="$1"
  if [ -f "$d/.worklogignore" ]; then printf 'IGNORED %s\n' "$d"; return; fi
  printf 'REPO %s\n' "$d"
  # 两步赋值：空仓时 rev-parse 会 stdout 输出 HEAD 且 exit 128，`|| echo` 拼接写法会产出两行破坏行协议
  br=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null) || br="unknown"
  printf 'BRANCH %s\n' "$br"
  out=$(${TIMEOUT_CMD[@]+"${TIMEOUT_CMD[@]}"} git -C "$d" log --branches --tags --fixed-strings \
        --since="$SINCE" --until="$UNTIL" \
        --date=iso-strict --pretty='format:%h|%ad|%an|%s' ${AUTHOR_ARGS[@]+"${AUTHOR_ARGS[@]}"} 2>/dev/null)
  rc=$?
  [ "$rc" -eq 124 ] && echo "TIMEOUT $d" >&2   # GNU timeout 的超时退出码；无 timeout 时不触发
  n_commits=0
  if [ -n "$out" ]; then
    while IFS= read -r line; do
      [ -n "$line" ] || continue
      printf 'COMMIT %s\n' "$line"
      n_commits=$((n_commits+1))
    done <<EOF
$out
EOF
  fi
  dirty=$(git -C "$d" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  printf 'DIRTY %s\n' "${dirty:-0}"
  if [ "$n_commits" -eq 0 ] && [ -n "$REF_FILE" ]; then
    hit=$(find "$d" -maxdepth 3 -type f -newer "$REF_FILE" ! -path '*/.git/*' -print 2>/dev/null | head -1)
    [ -n "$hit" ] && printf 'MTIME_ACTIVE\n'
  fi
}

for root in "$@"; do
  case "$root" in "~") root="$HOME" ;; "~/"*) root="$HOME/${root#\~/}" ;; esac
  if [ ! -d "$root" ]; then
    echo "SKIP_UNMOUNTED $root" >&2
    continue
  fi
  # 与 discover.sh 同一发现逻辑：prune 隐藏目录（.git 除外）与 node_modules；-mindepth 1 保护显式 root
  find "$root" -mindepth 1 -maxdepth "$MAXDEPTH" \
    \( -type d \( \( -name '.*' ! -name .git \) -o -name node_modules \) -prune \) -o \
    -type d -name .git -prune -print 2>/dev/null | sort | while IFS= read -r g; do
    scan_repo "${g%/.git}"
  done
done

[ -n "$REF_FILE" ] && rm -f "$REF_FILE"
exit 0
