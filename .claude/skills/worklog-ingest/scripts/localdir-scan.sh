#!/usr/bin/env bash
# worklog local-dir 源扫描器：非 git 目录（config 显式声明）按 mtime 判「窗口内有无活动」。
# presence 级信号，不读内容、不列文件名。自足单文件，可移植性纪律与 scan.sh 同源（BSD/GNU find
# 通用参数；不用 find -newermt；bash 3.2 兼容；见 pitfalls 库）。
#
# 用法:
#   bash localdir-scan.sh --from '<YYYYMMDDhhmm[.SS]>' --to '<YYYYMMDDhhmm[.SS]>' [--depth N] <path> [<path>...]
#
# 时间参数由调用方（Claude 按 config timezone 计算）传入 touch -t 格式，本脚本自身零日期运算。
# 活动判据：存在 mtime ∈ (from, to] 的普通文件（两个参照文件夹出窗口：find -newer 起 ! -newer 止）。
#   ⚠️ touch -t 按本进程时区解释数字：调用前必须 `export TZ=<config.timezone>`（Claude Code 沙箱
#      注入别的时区，裸调用会把窗口整体平移数小时、活动记到错误日期）
#   ⚠️ 上下界都必须给：只有下界的 find -newer 会把「目标日之后才动的目录」误判成目标日有活动，
#      「补充昨天 / 回填 N 天」必错账（这是本脚本取代 SKILL 内联配方的直接原因）
#   ⚠️ 调用方要半开窗口 [起, 止) 时，--to 须传窗口止减 1 秒（.SS 精度），与 scan.sh --until 同一纪律
# 噪音防护（与 scan.sh / discover.sh 同口径）：隐藏目录与 node_modules 整树跳过、隐藏文件（.DS_Store 等）
# 不算活动、深度默认 4：Finder 浏览、同步盘元数据抖动、依赖安装都不该被记成「今天动过这个项目」。
#
# 输出（stdout，行协议，供 LLM 汇编）:
#   LOCALDIR <abs-path>       一个已声明目录开始
#   MTIME_ACTIVE              （仅窗口内有活动时，紧跟所属 LOCALDIR 行）
# stderr:
#   SKIP_MISSING <path>       路径不存在（记一句 + 继续，常态路径）
set -uo pipefail
export LC_ALL=C

FROM="" TO="" MAXDEPTH=4
while [ $# -gt 0 ]; do
  case "$1" in
    --from) FROM="$2"; shift 2 ;;
    --to) TO="$2"; shift 2 ;;
    --depth) MAXDEPTH="$2"; shift 2 ;;
    --) shift; break ;;
    -*) echo "Unknown option: $1" >&2; exit 2 ;;
    *) break ;;
  esac
done
[ -n "$FROM" ] && [ -n "$TO" ] && [ $# -ge 1 ] || {
  echo "Usage: bash localdir-scan.sh --from <touch-t> --to <touch-t> [--depth N] <path>..." >&2
  exit 2
}
# 非数字深度会让 find 静默失败（2>/dev/null 吞报错），「无活动」与故障不可区分，前置校验
case "$MAXDEPTH" in ''|*[!0-9]*) echo "Bad --depth: $MAXDEPTH" >&2; exit 2 ;; esac

# 参照文件放 TMPDIR（绝不落用户目录：落 vault 会弄脏 git status、落被扫目录会自证活动）
REF_FROM="${TMPDIR:-/tmp}/worklog-localdir-from.$$"
REF_TO="${TMPDIR:-/tmp}/worklog-localdir-to.$$"
trap 'rm -f "$REF_FROM" "$REF_TO"' EXIT
# 先区分「TMPDIR 不可写」与「时间格式错」两种故障，报错才有自救方向
if ! : > "$REF_FROM" 2>/dev/null || ! : > "$REF_TO" 2>/dev/null; then
  echo "Cannot write reference files under ${TMPDIR:-/tmp} (check TMPDIR)" >&2
  exit 2
fi
if ! touch -t "$FROM" "$REF_FROM" 2>/dev/null || ! touch -t "$TO" "$REF_TO" 2>/dev/null; then
  echo "Bad --from/--to (touch -t format YYYYMMDDhhmm[.SS]): $FROM / $TO" >&2
  exit 2
fi

for p in "$@"; do
  # config 里的 ~ 原样传进来时兜底展开（仅 ~ 与 ~/ 前缀，与 scan.sh 同）；否则会被误报成路径不存在
  case "$p" in "~") p="$HOME" ;; "~/"*) p="$HOME/${p#\~/}" ;; esac
  if [ ! -d "$p" ]; then
    echo "SKIP_MISSING $p" >&2
    continue
  fi
  printf 'LOCALDIR %s\n' "$p"
  # -H：声明的路径本身是符号链接时解引用（与 scan.sh / discover.sh 同）
  hit=$(find -H "$p" -mindepth 1 -maxdepth "$MAXDEPTH" \
    \( -type d \( -name '.*' -o -name node_modules \) -prune \) -o \
    -type f ! -name '.*' -newer "$REF_FROM" ! -newer "$REF_TO" -print 2>/dev/null | head -1)
  [ -n "$hit" ] && printf 'MTIME_ACTIVE\n'
done
exit 0
