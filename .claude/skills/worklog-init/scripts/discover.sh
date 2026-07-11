#!/usr/bin/env bash
# 项目发现：在给定 roots 下有限深度自动发现 git 仓（只认 .git，非 git 项目走 config 显式声明，见 PRD §6.4）
# 用法：bash discover.sh <root> [<root>...]
# 输出（stdout，每行一条）：
#   PROJECT <abs-path>     发现的 git 项目
#   IGNORED <abs-path>     项目根含 .worklogignore（永久 exclude，优先级高于 config）
# stderr：SKIP_UNMOUNTED <root>（root 不存在 = 硬盘未挂载等，常态路径）
# 可移植性：BSD/GNU find 均支持 -maxdepth/-type/-name/-prune；不用 date -v / -newermt（见 pitfalls 库）
set -uo pipefail
# 注意语义：MAXDEPTH 计的是 find 深度，.git 比项目根深一层 → 项目有效发现深度 = MAXDEPTH-1
# 默认 4 = 覆盖 root/分类/项目 三级嵌套；roots 尽量给具体的项目父目录而非 $HOME
MAXDEPTH="${WORKLOG_DISCOVER_DEPTH:-4}"

[ $# -ge 1 ] || { echo "Usage: bash discover.sh <root> [<root>...]" >&2; exit 2; }

for root in "$@"; do
  # config 里的 ~ 原样传进来时兜底展开（仅 ~ 与 ~/ 前缀；~user 形式不支持，会落到 SKIP_UNMOUNTED）
  case "$root" in "~") root="$HOME" ;; "~/"*) root="$HOME/${root#\~/}" ;; esac
  if [ ! -d "$root" ]; then
    echo "SKIP_UNMOUNTED $root" >&2
    continue
  fi
  # 隐藏目录（.archive/.cache 等，.git 除外）与 node_modules 一律 prune：降噪 + 防 root=$HOME 时扫爆
  # -mindepth 1 保护显式给出的 root 本身（即便它是隐藏目录也不被 prune）
  # -H：root 本身是符号链接时解引用（[ -d ] 跟随符号链接而 find 默认 -P 不跟随，否则静默零输出）
  # -print0 + read -d ''：路径含换行时按行读会拆成幻影条目污染行协议；这类路径无法在行协议中表示，跳过并 stderr 告警
  find -H "$root" -mindepth 1 -maxdepth "$MAXDEPTH" \
    \( -type d \( \( -name '.*' ! -name .git \) -o -name node_modules \) -prune \) -o \
    -type d -name .git -prune -print0 2>/dev/null | while IFS= read -r -d '' g; do
    case "$g" in *$'\n'*) echo "SKIP_BADNAME path contains newline" >&2; continue ;; esac
    d="${g%/.git}"
    if [ -f "$d/.worklogignore" ]; then
      printf 'IGNORED %s\n' "$d"
    else
      printf 'PROJECT %s\n' "$d"
    fi
  done
done | sort -u
