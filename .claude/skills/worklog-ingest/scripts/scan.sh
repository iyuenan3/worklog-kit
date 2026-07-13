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
#   REPO <abs-path>                     一个 git 项目开始（嵌套子仓与 submodule 各自独立一段；
#                                       submodule 的 .git 是 gitdir: 指针文件、对象库独立，照常扫）
#   BRANCH <name>                       当前分支
#   COMMIT <short-hash>|<iso-date>|<author>|<subject>    窗口内 commit（--branches --tags，天然排除 refs/stash 伪 commit）
#       ⚠️ 消费方注意：| 分隔只取前三个，第四段 subject 为余部、本身可能含 |
#       ⚠️ --author 为 git 子串匹配（已加 --fixed-strings 关正则），非精确匹配
#       ⚠️ git 的 --until 是闭区间（<=）：调用方要半开窗口 [起, 止) 时，传入的 --until 须自行减 1 秒
#   DIRTY <n>                           未提交变更文件数（无 commit 但有活动的信号；
#                                       「内容全为嵌套仓」的未追踪目录是结构幻影、不计，见 scan_repo 内注释）
#   MTIME_ACTIVE                        （仅给了 --touch-since 且窗口内无 commit 时）文件 mtime 有动静
#                                       （隐藏目录 / node_modules / 隐藏文件 / 嵌套仓不算：Finder 的 .DS_Store、
#                                       依赖安装、子仓自身活动都不是本仓的活动信号）
#   IGNORED <abs-path>                  项目根或任一祖先目录含 .worklogignore（否决整棵子树，
#                                       嵌套子仓 / submodule / worktree 同享否决权）
# stderr:
#   SKIP_UNMOUNTED <root>               root 不存在（硬盘未挂载等，常态路径）
#   WORKTREE_SKIP <wt-path> -> <main-path>   worktree 检出不独立扫：与主仓共享 refs，双扫会重复计
#                                       COMMIT。第二段 = 主仓工作区路径（自 git-common-dir 推导），
#                                       消费方据此机械比对：主仓路径出现在任一 REPO / IGNORED 行即已
#                                       覆盖；主仓被 .worklogignore 否决时本信号整行不出（防路径泄漏）。
#                                       bare 仓（目录名非 .git）不被发现，属文档声明的边界
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
# --depth 非数字时 find 会静默失败（2>/dev/null 吞报错），零输出与「真没活动」不可区分，必须前置校验
case "$MAXDEPTH" in ''|*[!0-9]*) echo "Bad --depth: $MAXDEPTH" >&2; exit 2 ;; esac

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

# .worklogignore 否决整棵子树：项目根或任一祖先目录含标记即 exclude（PRD §6.4 项目侧否决权；
# 嵌套子仓与 submodule 独立成项后，用户在树顶放一个标记应当继续罩住整棵树）
is_ignored() {
  ip="$1"
  while :; do
    [ -f "$ip/.worklogignore" ] && return 0
    case "$ip" in ""|"/"|".") return 1 ;; esac
    ip=$(dirname "$ip")
  done
}

scan_repo() {
  d="$1"
  if is_ignored "$d"; then printf 'IGNORED %s\n' "$d"; return; fi
  printf 'REPO %s\n' "$d"
  # 两步赋值：空仓时 rev-parse 会 stdout 输出 HEAD 且 exit 128，`|| echo` 拼接写法会产出两行破坏行协议
  br=$(git -C "$d" rev-parse --abbrev-ref HEAD 2>/dev/null) || br="unknown"
  printf 'BRANCH %s\n' "$br"
  # --abbrev=7 固定短哈希长度：与 github-scan.sh 的 sha[0:7] 对齐，跨源按短哈希去重才不会因长度漂移失配
  out=$(${TIMEOUT_CMD[@]+"${TIMEOUT_CMD[@]}"} git -C "$d" log --branches --tags --fixed-strings --abbrev=7 \
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
  # DIRTY 过滤嵌套仓幻影：git 不追踪嵌套仓内容，含嵌套仓的未追踪目录会作为一行 `?? sub/` 永久出现，
  # 父仓自身零活动也带信号（presence 级永远到不了「无信号可省略」）。判据：`?? <dir>/` 条目若目录内
  # 除嵌套仓子树（.git 目录或文件形态）外无任何非目录条目（普通文件 / 符号链接均算真实内容）→ 结构
  # 幻影，不计；否则照常计。已追踪的 gitlink 漂移（` M sub`）是父仓待提交的真实变更，照常计。
  # 用 --porcelain -z 解析：普通 --porcelain 对含空格 / 非 ASCII 的路径整体加引号且尾斜杠在引号内，
  # `?? <dir>/` 模式匹配不到（macOS 空格目录名与中文目录名是常态，不是边角）；-z 永不引号转义。
  # -z 下 rename / copy（XY 以 R / C 开头）是「新路径 NUL 旧路径」双段记录，须多吞一段免双计。
  dirty=0
  while IFS= read -r -d '' sl; do
    [ -n "$sl" ] || continue
    case "$sl" in
      R*|C*)
        IFS= read -r -d '' _rename_src || true
        dirty=$((dirty+1)) ;;
      '?? '*'/')
        p="${sl#\?\? }"; p="${p%/}"
        extra=$(find "$d/$p" \( -type d -exec sh -c '[ -e "$1/.git" ]' _ {} \; -prune \) -o \
                ! -type d -print 2>/dev/null | head -1)
        [ -n "$extra" ] && dirty=$((dirty+1)) ;;
      *) dirty=$((dirty+1)) ;;
    esac
  done < <(git -C "$d" status --porcelain -z 2>/dev/null)
  printf 'DIRTY %s\n' "$dirty"
  if [ "$n_commits" -eq 0 ] && [ -n "$REF_FILE" ]; then
    # 噪音防护：隐藏目录（含 .git）/ node_modules / 嵌套仓整树跳过，隐藏文件（.DS_Store 等）不算
    # 活动：mtime 是弱兜底信号，Finder 浏览与依赖安装不该制造假活动。隐藏目录与 node_modules 的
    # 口径与 localdir-scan.sh 一致；嵌套仓 prune 是本脚本特有（子仓已独立成 REPO 段，活动各归各）
    hit=$(find "$d" -mindepth 1 -maxdepth 3 \
      \( -type d \( -name '.*' -o -name node_modules -o -exec sh -c '[ -e "$1/.git" ]' _ {} \; \) -prune \) -o \
      -type f ! -name '.*' -newer "$REF_FILE" -print 2>/dev/null | head -1)
    [ -n "$hit" ] && printf 'MTIME_ACTIVE\n'
  fi
}

# find 发现的 .git 有目录 / 文件两种形态。文件 = gitdir: 指针（submodule / linked worktree /
# separate-git-dir）。worktree 判定必须语义化而非 gitdir 路径子串匹配 /worktrees/：后者会误伤
# 「--separate-git-dir 到名含 worktrees 的目录」与「worktree 内 submodule」这两类独立对象库
# （commit 静默丢失）。语义判据：git-dir == git-common-dir ⇔ 独立对象库 → 照常扫；
# 不等 ⇔ linked worktree → 不独立扫（与主仓共享 refs，双扫会重复计 COMMIT），信号带主仓
# 工作区路径供消费方机械比对；主仓被 .worklogignore 否决时静默（不泄漏被排除项目的路径）。
handle_git_path() {
  gp="$1"
  wd="${gp%/.git}"
  if [ -f "$gp" ]; then
    case "$(head -n 1 "$gp" 2>/dev/null)" in
      gitdir:*) : ;;
      *) return ;;   # 恰好叫 .git 的杂文件
    esac
    gd=$(git -C "$wd" rev-parse --absolute-git-dir 2>/dev/null) || gd=""
    cdir=$(git -C "$wd" rev-parse --git-common-dir 2>/dev/null) || cdir=""
    case "$cdir" in ""|/*) : ;; *) cdir="$wd/$cdir" ;; esac   # --git-common-dir 可能给相对路径
    gd_n=$(cd "$gd" 2>/dev/null && pwd -P) || gd_n=""
    cd_n=$(cd "$cdir" 2>/dev/null && pwd -P) || cd_n=""
    if [ -n "$gd_n" ] && [ -n "$cd_n" ] && [ "$gd_n" != "$cd_n" ]; then
      main="${cd_n%/.git}"   # bare 主仓（如 proj.git）无 /.git 尾巴，保留原路径即其身份
      if is_ignored "$wd"; then
        printf 'IGNORED %s\n' "$wd"
      elif is_ignored "$main"; then
        :   # 主仓被否决：整条信号不出
      else
        echo "WORKTREE_SKIP $wd -> $main" >&2
      fi
      return
    fi
  fi
  scan_repo "$wd"
}

# 先收集全部 root 的 .git 路径再全局去重：roots 嵌套（如 ~/code 与 ~/code/work）时
# 同一仓会被发现两次，COMMIT 有 hash 去重兜底但 DIRTY 计数会翻倍、REPO 块重复污染下游
GIT_LIST="${TMPDIR:-/tmp}/worklog-scan-gits.$$"
: > "$GIT_LIST" 2>/dev/null || GIT_LIST=""
for root in "$@"; do
  # 仅展开 ~ 与 ~/ 前缀；~user 形式不支持（会落到 SKIP_UNMOUNTED）
  case "$root" in "~") root="$HOME" ;; "~/"*) root="$HOME/${root#\~/}" ;; esac
  if [ ! -d "$root" ]; then
    echo "SKIP_UNMOUNTED $root" >&2
    continue
  fi
  # 与 discover.sh 同一发现逻辑：prune 隐藏目录（.git 除外）与 node_modules；-mindepth 1 保护显式 root
  # .git 同时匹配目录与文件形态（后者 = submodule / worktree / separate-git-dir 指针，由 handle_git_path 分类）
  # -H：root 本身是符号链接时解引用（[ -d ] 跟随符号链接而 find 默认 -P 不跟随，否则静默零输出）
  # -print0 + read -d ''：路径含换行时按行读会拆成幻影条目污染行协议；这类路径无法在行协议中表示，跳过并 stderr 告警
  if [ -n "$GIT_LIST" ]; then
    find -H "$root" -mindepth 1 -maxdepth "$MAXDEPTH" \
      \( -type d \( \( -name '.*' ! -name .git \) -o -name node_modules \) -prune \) -o \
      \( -type d -name .git -prune -o -type f -name .git \) -print0 2>/dev/null >> "$GIT_LIST"
  else
    # 临时文件不可写的降级路径：退回逐 root 处理（嵌套 roots 会重复，属罕见环境的已知限制）
    find -H "$root" -mindepth 1 -maxdepth "$MAXDEPTH" \
      \( -type d \( \( -name '.*' ! -name .git \) -o -name node_modules \) -prune \) -o \
      \( -type d -name .git -prune -o -type f -name .git \) -print0 2>/dev/null | sort -z | while IFS= read -r -d '' g; do
      case "$g" in *$'\n'*) echo "SKIP_BADNAME path contains newline" >&2; continue ;; esac
      handle_git_path "$g"
    done
  fi
done
if [ -n "$GIT_LIST" ]; then
  sort -zu "$GIT_LIST" | while IFS= read -r -d '' g; do
    case "$g" in *$'\n'*) echo "SKIP_BADNAME path contains newline" >&2; continue ;; esac
    handle_git_path "$g"
  done
  rm -f "$GIT_LIST"
fi

[ -n "$REF_FILE" ] && rm -f "$REF_FILE"
exit 0
