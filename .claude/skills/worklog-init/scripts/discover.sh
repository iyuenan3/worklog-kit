#!/usr/bin/env bash
# 项目发现：在给定 roots 下有限深度自动发现 git 仓（只认 .git，非 git 项目走 config 显式声明，见 PRD §6.4）
# 用法：bash discover.sh <root> [<root>...]
# 输出（stdout，每行一条）：
#   PROJECT <abs-path>     发现的 git 项目（嵌套子仓与 submodule 各自独立成项；submodule 的 .git 是
#                          gitdir: 指针文件、对象库独立，与 .git 目录形态同等对待）
#   IGNORED <abs-path>     项目根或任一祖先目录含 .worklogignore（否决整棵子树，优先级高于 config）
# stderr：SKIP_UNMOUNTED <root>（root 不存在 = 硬盘未挂载等，常态路径）
#         WORKTREE_SKIP <wt-path> -> <main-path>（worktree 检出不独立成项：与主仓共享 refs，commit
#         经主仓捕获；第二段 = 主仓工作区路径，主仓不在预览清单时 init 应提示补 root；主仓被
#         .worklogignore 否决时整行不出。bare 仓不被发现，属文档声明的边界）
# 可移植性：BSD/GNU find 均支持 -maxdepth/-type/-name/-prune；不用 date -v / -newermt（见 pitfalls 库）
set -uo pipefail
# 注意语义：MAXDEPTH 计的是 find 深度，.git 比项目根深一层 → 项目有效发现深度 = MAXDEPTH-1
# 默认 4 = 覆盖 root/分类/项目 三级嵌套；roots 尽量给具体的项目父目录而非 $HOME
MAXDEPTH="${WORKLOG_DISCOVER_DEPTH:-4}"
# 非数字深度会让 find 静默失败（2>/dev/null 吞报错），空输出与「真没项目」不可区分，前置校验
case "$MAXDEPTH" in ''|*[!0-9]*) echo "Bad WORKLOG_DISCOVER_DEPTH: $MAXDEPTH" >&2; exit 2 ;; esac

[ $# -ge 1 ] || { echo "Usage: bash discover.sh <root> [<root>...]" >&2; exit 2; }

# .worklogignore 否决整棵子树（与 scan.sh 的 is_ignored 同一纪律）
is_ignored() {
  ip="$1"
  while :; do
    [ -f "$ip/.worklogignore" ] && return 0
    case "$ip" in ""|"/"|".") return 1 ;; esac
    ip=$(dirname "$ip")
  done
}

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
  # .git 同时匹配目录与文件形态；文件 = gitdir: 指针（submodule / worktree / separate-git-dir），
  # 分类纪律与 scan.sh 的 handle_git_path 一致：worktree 判定语义化（git-dir == git-common-dir ⇔
  # 独立对象库照常成项；不等 ⇔ linked worktree 出 WORKTREE_SKIP），gitdir 路径子串匹配会误伤独立对象库
  find -H "$root" -mindepth 1 -maxdepth "$MAXDEPTH" \
    \( -type d \( \( -name '.*' ! -name .git \) -o -name node_modules \) -prune \) -o \
    \( -type d -name .git -prune -o -type f -name .git \) -print0 2>/dev/null | while IFS= read -r -d '' g; do
    case "$g" in *$'\n'*) echo "SKIP_BADNAME path contains newline" >&2; continue ;; esac
    d="${g%/.git}"
    if [ -f "$g" ]; then
      case "$(head -n 1 "$g" 2>/dev/null)" in
        gitdir:*) : ;;
        *) continue ;;   # 恰好叫 .git 的杂文件
      esac
      gd=$(git -C "$d" rev-parse --absolute-git-dir 2>/dev/null) || gd=""
      cdir=$(git -C "$d" rev-parse --git-common-dir 2>/dev/null) || cdir=""
      case "$cdir" in ""|/*) : ;; *) cdir="$d/$cdir" ;; esac
      gd_n=$(cd "$gd" 2>/dev/null && pwd -P) || gd_n=""
      cd_n=$(cd "$cdir" 2>/dev/null && pwd -P) || cd_n=""
      if [ -n "$gd_n" ] && [ -n "$cd_n" ] && [ "$gd_n" != "$cd_n" ]; then
        main="${cd_n%/.git}"
        if is_ignored "$d"; then
          printf 'IGNORED %s\n' "$d"
        elif is_ignored "$main"; then
          :   # 主仓被否决：整条信号不出
        else
          echo "WORKTREE_SKIP $d -> $main" >&2
        fi
        continue
      fi
    fi
    if is_ignored "$d"; then
      printf 'IGNORED %s\n' "$d"
    else
      printf 'PROJECT %s\n' "$d"
    fi
  done
done | sort -u
