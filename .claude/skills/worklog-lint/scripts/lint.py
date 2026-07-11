#!/usr/bin/env python3
"""worklog vault lint（通用机械项）。

用法:
    python3 lint.py [--vault <dir>]     # 缺省: git toplevel，再退 cwd

检查项与级别（与 check.sh 系约定一致：🔴 must-fix → exit 1；🟡 advisory → exit 0）:
  🔴 契约锚点缺失: wiki/index.md 三段标题 / wiki/log.md ingest 锚点 / wiki/todos.md 分区（zh/en 任一 locale 命中即可）
  🔴 疑似凭证泄漏: diaries/ wiki/ inbox/ 与两层 config（模式含 sk- / ghp_ / AKIA / Bearer / api_key= 等，含截断 token 前缀风险）
  🔴 diary frontmatter 缺 date
  🟡 断链 [[...]]（目标不在 wiki/ 与 diaries/ 内；跨库引用属正常，故仅提示）
  🟡 项目页 frontmatter 缺 last_updated / source_count / diaries
  🟡 wiki/log.md 超 1500 行（该按年轮转了）

zh 写作门（标点 / 日期）不在本脚本：由 worklog-lint SKILL 按 config language 追加调用。
"""
import os
import re
import sys
import subprocess


def vault_root(argv):
    if len(argv) >= 3 and argv[1] == "--vault":
        return os.path.abspath(argv[2])
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except Exception:
        return os.getcwd()


SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{12,}"
    r"|Bearer[ \t]+[A-Za-z0-9._-]{16,}"
    r"|(api[_-]?key|secret|token|password)[ \t]*[:=][ \t]*['\"]?[A-Za-z0-9._-]{16,})",
    re.IGNORECASE,
)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")

ANCHORS = {
    "wiki/index.md": [("## 最后更新", "## Latest"), ("## 项目", "## Projects"), ("## 日记", "## Diaries")],
    "wiki/log.md": [("ingest:log-anchor", "ingest:log-anchor")],
    "wiki/todos.md": [("## 进行中", "## In progress"), ("## 待办", "## Backlog")],
}


def md_files(root, sub):
    base = os.path.join(root, sub)
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for f in sorted(filenames):
            if f.endswith(".md"):
                yield os.path.join(dirpath, f)


def main():
    root = vault_root(sys.argv)
    hard, soft = [], []

    # 1. 契约锚点
    for rel, pairs in ANCHORS.items():
        p = os.path.join(root, rel)
        if not os.path.isfile(p):
            hard.append(f"{rel}: 契约文件缺失")
            continue
        text = open(p, encoding="utf-8", errors="replace").read()
        for zh, en in pairs:
            if zh not in text and en not in text:
                hard.append(f"{rel}: 缺锚点「{zh} / {en}」（ingest 写入依赖）")

    # 收集 wikilink 可解析目标：wiki 各页 stem + 日记日期 stem
    targets = set()
    for area in ("wiki", "diaries"):
        for p in md_files(root, area):
            targets.add(os.path.splitext(os.path.basename(p))[0])

    # 2. 逐文件扫描（凭证 / 断链 / frontmatter）
    scan_areas = ["diaries", "wiki", "inbox"]
    for area in scan_areas:
        for p in md_files(root, area):
            rel = os.path.relpath(p, root)
            text = open(p, encoding="utf-8", errors="replace").read()
            for i, line in enumerate(text.splitlines(), 1):
                if SECRET_RE.search(line):
                    hard.append(f"{rel}:{i}: 疑似明文凭证，立即移除")
            # 断链扫描剥掉代码块与行内代码（语法示例不算链接）；凭证扫描保留全文不剥
            text_links = re.sub(r"```.*?```", "", text, flags=re.S)
            text_links = re.sub(r"`[^`\n]*`", "", text_links)
            for m in WIKILINK_RE.finditer(text_links):
                t = m.group(1).strip()
                if t and t not in targets:
                    soft.append(f"{rel}: 断链 [[{t}]]（目标不在 vault 内；跨库引用可忽略）")
            del text_links

    for cfg in ("worklog.config.yaml", "worklog.config.local.yaml"):
        p = os.path.join(root, cfg)
        if os.path.isfile(p):
            for i, line in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                if SECRET_RE.search(line):
                    tag = "🔴" if cfg.endswith("config.yaml") else "🟡"
                    (hard if tag == "🔴" else soft).append(
                        f"{cfg}:{i}: 疑似凭证（{'该文件入 git，绝不能放凭证' if tag == '🔴' else 'local 层不入 git，但仍建议复核'}）")

    # 3. diary frontmatter
    for p in md_files(root, "diaries"):
        rel = os.path.relpath(p, root)
        head = open(p, encoding="utf-8", errors="replace").read(400)
        ok = False
        if head.startswith("---") and head.count("---") >= 2:
            ok = "date:" in head.split("---")[1]
        if not ok:
            hard.append(f"{rel}: frontmatter 缺失或缺 date")

    # 4. 项目页 frontmatter
    projdir = os.path.join(root, "wiki", "projects")
    if os.path.isdir(projdir):
        for f in sorted(os.listdir(projdir)):
            if not f.endswith(".md"):
                continue
            head = open(os.path.join(projdir, f), encoding="utf-8", errors="replace").read(600)
            missing = [k for k in ("last_updated", "source_count", "diaries") if k not in head]
            if missing:
                soft.append(f"wiki/projects/{f}: frontmatter 缺 {'/'.join(missing)}")

    # 5. log.md 轮转阈值
    logp = os.path.join(root, "wiki", "log.md")
    if os.path.isfile(logp):
        n = sum(1 for _ in open(logp, encoding="utf-8", errors="replace"))
        if n > 1500:
            soft.append(f"wiki/log.md: {n} 行，超过 1500，建议按年轮转为 log-YYYY.md")

    for msg in hard:
        print(f"🔴 {msg}")
    for msg in soft:
        print(f"🟡 {msg}")
    print("----")
    print(f"🔴 {len(hard)} must-fix / 🟡 {len(soft)} advisory")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
