#!/usr/bin/env bash
# GitHub 收集器：扫窗口内「我名下所有可访问仓的 push」，任何设备产生的工作只要 push 了就被发现。
# 两段式：① user/repos 按 pushed 降序发现窗口内活跃仓 ② 逐仓 commits API 按窗口 + author=账号 精扫
#   （author 用 GitHub 账号维度过滤，天然覆盖该账号关联的全部 email，identities 不必逐个传）
#
# 用法: bash github-scan.sh --since-utc <ISO-Z> --until-utc <ISO-Z> [--account <login>] [--max-repos 100]
#   时间一律传 UTC Z 格式（GitHub API 的 pushed_at / commits 均为 UTC；调用方负责时区换算，本脚本零日期运算；
#   --until-utc 沿用调用方「减 1 秒」约定保半开语义）
#
# 输出行协议（与 scan.sh 对齐；消费方按 commit 短哈希（7 位）跨源去重，本地扫描优先）:
#   REPO gh:<owner>/<repo>
#   COMMIT <short-sha>|<iso-date>|<author-name>|<subject 首行>
#       ⚠️ 消费方注意：| 分隔只取前三个，第四段 subject 为余部、本身可能含 |
# 已知盲区（写进晨报提示）：author=账号 只匹配该账号已关联（verified）的 email；
#   某设备 git config 用了未关联邮箱的 commit 会被漏掉 → 建议在 GitHub Settings > Emails 补全
# 规模上限（设计决策）：仓发现单页 per_page（GitHub 上限 100）、单仓 commits 单页 100，超限走
#   TRUNCATED 提示不翻页（个人日常规模远够；回填长窗口时留意 stderr）
# stderr + 退出码:
#   exit 0 正常（TRUNCATED / REPO_SKIP 提示走 stderr）/ exit 2 用法错
#   exit 3 AUTH_FAIL 或 API_FAIL（未认证或 repos API 失败，stderr 区分）/ exit 4 NO_GH
set -uo pipefail
export LC_ALL=C

SINCE_UTC="" UNTIL_UTC="" ACCOUNT="" MAX_REPOS=100
while [ $# -gt 0 ]; do
  case "$1" in
    --since-utc) SINCE_UTC="$2"; shift 2 ;;
    --until-utc) UNTIL_UTC="$2"; shift 2 ;;
    --account) ACCOUNT="$2"; shift 2 ;;
    --max-repos) MAX_REPOS="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
[ -n "$SINCE_UTC" ] && [ -n "$UNTIL_UTC" ] || {
  echo "Usage: bash github-scan.sh --since-utc <ISO-Z> --until-utc <ISO-Z> [--account <login>]" >&2
  exit 2
}

command -v gh >/dev/null 2>&1 || { echo "NO_GH" >&2; exit 4; }
gh auth status >/dev/null 2>&1 || { echo "AUTH_FAIL" >&2; exit 3; }
if [ -z "$ACCOUNT" ]; then
  ACCOUNT=$(gh api user --jq .login 2>/dev/null) || true
  [ -n "$ACCOUNT" ] || { echo "AUTH_FAIL" >&2; exit 3; }
fi

# 阶段 1 · 发现：可访问仓（含 org / collaborator）按 pushed 降序取首页，窗口内活跃仓在个人规模下必在前列
repos=$(gh api "user/repos?sort=pushed&direction=desc&per_page=$MAX_REPOS" \
        --jq ".[] | select(.pushed_at >= \"$SINCE_UTC\") | .full_name" 2>/dev/null) \
  || { echo "API_FAIL user/repos" >&2; exit 3; }

count=$(printf '%s' "$repos" | grep -c . 2>/dev/null); count=${count:-0}
[ "$count" -ge "$MAX_REPOS" ] && echo "TRUNCATED active-repos>=$MAX_REPOS, some may be missed" >&2

# 阶段 2 · 精扫：逐仓按窗口 + author 拉 commits；单仓失败（rate limit / 权限 / 空仓 409）跳过继续并计数
# for 分词安全：repo full_name 不含空格；不用 pipe|while（子 shell 会丢 skip 计数）
skip=0
for full in $repos; do
  [ -n "$full" ] || continue
  commits=$(gh api "repos/$full/commits?since=$SINCE_UTC&until=$UNTIL_UTC&author=$ACCOUNT&per_page=100" \
    --jq '.[] | .sha[0:7] + "|" + .commit.author.date + "|" + .commit.author.name + "|" + (.commit.message | split("\n")[0])' \
    2>/dev/null) || { skip=$((skip+1)); continue; }
  [ -n "$commits" ] || continue
  printf 'REPO gh:%s\n' "$full"
  c_count=0
  printf '%s\n' "$commits" | while IFS= read -r c; do
    [ -n "$c" ] && printf 'COMMIT %s\n' "$c"
  done
  c_count=$(printf '%s' "$commits" | grep -c . 2>/dev/null); c_count=${c_count:-0}
  [ "$c_count" -ge 100 ] && echo "TRUNCATED commits>=100 for $full" >&2
done
[ "$skip" -gt 0 ] && echo "REPO_SKIP $skip repos failed (rate-limit / permission / empty)" >&2
exit 0
