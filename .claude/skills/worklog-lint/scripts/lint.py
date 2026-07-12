#!/usr/bin/env python3
"""worklog vault lint（通用机械项 + 健康节）。

用法:
    python3 lint.py [--vault <dir>]                     # 正误节。缺省 vault: git toplevel，再退 cwd
    python3 lint.py --health [--vault <dir>] [--today YYYY-MM-DD]   # 健康节（vault 体检，PRD §18）

正误节检查项与级别（与 check.sh 系约定一致：🔴 must-fix → exit 1；🟡 advisory → exit 0）:
  🔴 契约锚点缺失: wiki/index.md 三段标题 / wiki/log.md ingest 锚点 / wiki/todos.md 分区（zh/en 任一 locale 命中即可）
  🔴 疑似凭证泄漏: diaries/ wiki/ inbox/ 与两层 config（模式含 sk- / ghp_ / AKIA / Bearer / api_key= 等，含截断 token 前缀风险）
  🔴 diary frontmatter 缺 date
  🟡 断链 [[...]]（目标不在 wiki/ 与 diaries/ 内；跨库引用属正常，故仅提示）
  🟡 项目页 frontmatter 缺 last_updated / source_count / diaries
  🟡 wiki/log.md 超 1500 行（该按年轮转了）

健康节（--health）: 五项腐坏指标，零 LLM 纯脚本，阈值读 config `maintenance:` 段（缺省用内置默认）:
  🩺 状态漂移 / 孤儿页 / 实体分裂候选 / 膨胀（体积 + 决策日志条数）/ TODO 年龄
  退出码: 0 = 健康，2 = 有待维护项（1 保留给正误节 must-fix）；末行 `🩺 N 项待维护` 供脚本消费。
  --today 供测试固定「今天」；缺省按 config timezone 取当日。

zh 写作门（标点 / 日期）不在本脚本：由 worklog-lint SKILL 按 config language 追加调用。
"""
import datetime
import os
import re
import sys
import subprocess
import unicodedata


def parse_argv(argv):
    vault, health, today = None, False, None
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--vault" and i + 1 < len(argv):
            vault = os.path.abspath(argv[i + 1])
            i += 2
        elif a == "--health":
            health = True
            i += 1
        elif a == "--today" and i + 1 < len(argv):
            today = argv[i + 1]
            i += 2
        else:
            i += 1
    return vault, health, today


def default_root():
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


def main(root):
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
                # 行内 lint:ignore 标记豁免（写文档示例用；仅正文区生效，config 不豁免）
                if SECRET_RE.search(line) and "lint:ignore" not in line:
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

    # 3. diary frontmatter（逐行读到闭合 ---，不用定长 read(N)：长 frontmatter 会被截断而误报缺失）
    for p in md_files(root, "diaries"):
        rel = os.path.relpath(p, root)
        # 只对日记命名的文件做硬检查：Obsidian 同步冲突副本等杂件不该把 lint 卡成红
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", os.path.basename(p)):
            soft.append(f"{rel}: 非日记命名（同步冲突副本或手工文件？），跳过 frontmatter 检查")
            continue
        ok = False
        with open(p, encoding="utf-8", errors="replace") as fh:
            if fh.readline().strip() == "---":
                seen_date = False
                for _ in range(200):
                    line = fh.readline()
                    if not line:
                        break
                    if line.strip() == "---":
                        ok = seen_date
                        break
                    if line.startswith("date:"):
                        seen_date = True
        if not ok:
            hard.append(f"{rel}: frontmatter 缺失或缺 date")

    # 4. 项目页 frontmatter
    projdir = os.path.join(root, "wiki", "projects")
    if os.path.isdir(projdir):
        for f in sorted(os.listdir(projdir)):
            if not f.endswith(".md"):
                continue
            head = open(os.path.join(projdir, f), encoding="utf-8", errors="replace").read(2000)
            missing = [k for k in ("last_updated", "source_count", "diaries") if k not in head]
            if missing:
                soft.append(f"wiki/projects/{f}: frontmatter 缺 {'/'.join(missing)}")

    # 5. 增长文件阈值（log 轮转 + index 日记表年归档）
    logp = os.path.join(root, "wiki", "log.md")
    if os.path.isfile(logp):
        n = sum(1 for _ in open(logp, encoding="utf-8", errors="replace"))
        if n > 1500:
            soft.append(f"wiki/log.md: {n} 行，超过 1500，建议按年轮转为 log-YYYY.md")
    idxp = os.path.join(root, "wiki", "index.md")
    if os.path.isfile(idxp):
        n = sum(1 for _ in open(idxp, encoding="utf-8", errors="replace"))
        if n > 800:
            soft.append(f"wiki/index.md: {n} 行，日记表建议按年归档（旧年份行移入 index-<YYYY>.md），防无限增长")

    for msg in hard:
        print(f"🔴 {msg}")
    for msg in soft:
        print(f"🟡 {msg}")
    print("----")
    print(f"🔴 {len(hard)} must-fix / 🟡 {len(soft)} advisory")
    return 1 if hard else 0


# ── 健康节（--health）：五项腐坏指标，零 LLM（PRD §18；断链等正误项归上方正误节，不在此重复） ──

HEALTH_DEFAULTS = {
    "drift_days": 14,          # 状态漂移：项目页 last_updated 落后最近提及日记的天数
    "orphan_days": 60,         # 孤儿页：N 天无日记引用且无 wiki 入链
    "bloat_kb": 50,            # 膨胀：单页体积（KB）
    "decision_log_max": 30,    # 膨胀：项目页决策日志条数
    "todo_stale_days": [30, 90],  # TODO 年龄分档
}
DATE_FULL_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
DECISION_HEADS = ("决策日志", "Decision log")


def _parse_scalar(v):
    v = v.split("#", 1)[0].strip()
    if v.startswith("[") and v.endswith("]"):
        out = []
        for part in v[1:-1].split(","):
            part = part.strip()
            if part:
                try:
                    out.append(int(part))
                except ValueError:
                    pass
        return out or None
    try:
        return int(v)
    except ValueError:
        return v.strip("'\"") or None


def load_health_config(root):
    """读两层 config 的 maintenance: 块（local 覆盖同名键）+ 顶层 timezone。全键可选，缺省用默认值。"""
    cfg = dict(HEALTH_DEFAULTS)
    tz = None
    for name in ("worklog.config.yaml", "worklog.config.local.yaml"):
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            continue
        in_block = False
        for raw in open(p, encoding="utf-8", errors="replace"):
            line = raw.rstrip("\n")
            if not line.startswith((" ", "\t")):
                if line.startswith("timezone:"):
                    v = _parse_scalar(line.split(":", 1)[1])
                    if isinstance(v, str):
                        tz = v
                in_block = line.split("#", 1)[0].strip() == "maintenance:"
                continue
            if not in_block:
                continue
            s = line.strip()
            if not s or s.startswith("#") or ":" not in s:
                continue
            k, v = s.split(":", 1)
            k = k.strip()
            if k in HEALTH_DEFAULTS:
                pv = _parse_scalar(v)
                if isinstance(HEALTH_DEFAULTS[k], list):
                    if isinstance(pv, list) and pv:
                        cfg[k] = sorted(pv)
                elif isinstance(pv, int):
                    cfg[k] = pv
    return cfg, tz


def _frontmatter(text):
    if not text.startswith("---"):
        return {}
    out = {}
    for line in text.splitlines()[1:80]:
        if line.strip() == "---":
            break
        if ":" in line and not line.startswith((" ", "\t")):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def _to_date(s):
    m = DATE_FULL_RE.search(s or "")
    if not m:
        return None
    try:
        return datetime.date.fromisoformat(m.group(0))
    except ValueError:
        return None


def _links(text):
    """提取 wikilink 目标，剥代码块与行内代码（与正误节断链检查同规）。"""
    t = re.sub(r"```.*?```", "", text, flags=re.S)
    t = re.sub(r"`[^`\n]*`", "", t)
    return {m.group(1).strip() for m in WIKILINK_RE.finditer(t) if m.group(1).strip()}


def _norm(name):
    """形态学归一化（分裂候选用）：NFKC 折叠全半角 + 小写 + 去空格连字符下划线。中英别名超出机械能力，留给 maintain 的 LLM。"""
    s = unicodedata.normalize("NFKC", name).lower()
    return re.sub(r"[\s\-_]+", "", s)


def run_health(root, today_arg):
    cfg, tz = load_health_config(root)
    if today_arg:
        today = datetime.date.fromisoformat(today_arg)
    else:
        if tz:
            os.environ["TZ"] = tz
            try:
                import time as _time
                _time.tzset()
            except AttributeError:
                pass  # 非 Unix 平台无 tzset；产品面仅 macOS / Linux
        today = datetime.date.today()

    items = []

    # 素材收集
    diaries = {}
    for p in md_files(root, "diaries"):
        b = os.path.basename(p)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", b):
            d = _to_date(b)
            if d:
                diaries[d] = open(p, encoding="utf-8", errors="replace").read()
    diary_links = {d: _links(t) for d, t in diaries.items()}

    wiki = {}
    for p in md_files(root, "wiki"):
        rel = os.path.relpath(p, root).replace(os.sep, "/")
        wiki[rel] = open(p, encoding="utf-8", errors="replace").read()

    def stem(rel):
        return os.path.splitext(os.path.basename(rel))[0]

    def structural(rel):
        s = stem(rel)
        return rel.count("/") == 1 and (s in ("index", "todos") or s == "log" or s.startswith("log-"))

    def archived(rel):
        return rel.startswith("wiki/archive/")

    fm = {rel: _frontmatter(t) for rel, t in wiki.items()}
    alias_pages = {rel for rel, f in fm.items() if f.get("alias_of")}
    alias_stems = {stem(rel) for rel in alias_pages}
    wiki_links = {rel: _links(t) for rel, t in wiki.items() if not archived(rel)}
    live = sorted(rel for rel in wiki
                  if not structural(rel) and not archived(rel) and rel not in alias_pages)

    # 1. 状态漂移（项目页 last_updated vs 最近提及它的日记）
    for rel in live:
        if not rel.startswith("wiki/projects/"):
            continue
        lu = _to_date(fm[rel].get("last_updated", ""))
        mentions = [d for d, links in diary_links.items() if stem(rel) in links]
        if lu and mentions:
            gap = (max(mentions) - lu).days
            if gap > cfg["drift_days"]:
                items.append(f"状态漂移: {rel} last_updated {lu} 落后最近提及日记 {max(mentions)}"
                             f"（{gap} 天 > {cfg['drift_days']}）")

    # 2. 孤儿页（窗口内无日记引用 + 无 wiki 入链 + 页本身也不新鲜）
    for rel in live:
        st = stem(rel)
        inbound = any(st in links for r2, links in wiki_links.items() if r2 != rel)
        recent = any(st in links and (today - d).days <= cfg["orphan_days"]
                     for d, links in diary_links.items())
        lu = _to_date(fm[rel].get("last_updated", ""))
        if not inbound and not recent and (lu is None or (today - lu).days > cfg["orphan_days"]):
            items.append(f"孤儿页: {rel} {cfg['orphan_days']} 天内无日记引用且无 wiki 入链（可归档或补入链）")

    # 3. 实体分裂候选（活跃链接面：近窗日记 + 存活 wiki + 存活页名；alias 存根 = 已处理别名，跳过）
    active_names = set()
    for d, links in diary_links.items():
        if (today - d).days <= cfg["orphan_days"]:
            active_names |= links
    for rel in wiki:
        if not archived(rel) and rel not in alias_pages:
            active_names |= wiki_links.get(rel, set())
    active_names |= {stem(rel) for rel in live}
    groups = {}
    for name in active_names:
        if DATE_FULL_RE.fullmatch(name) or name in alias_stems:
            continue
        key = _norm(name)
        if key:
            groups.setdefault(key, set()).add(name)
    for key in sorted(groups):
        forms = groups[key]
        if len(forms) >= 2:
            items.append(f"实体分裂候选: {' / '.join(sorted(forms))}（归一化后同名，建议合并重链）")

    # 4. 膨胀（体积 + 项目页决策日志条数）
    for rel in live:
        kb = os.path.getsize(os.path.join(root, rel)) / 1024
        if kb > cfg["bloat_kb"]:
            items.append(f"膨胀: {rel} {kb:.0f}KB > {cfg['bloat_kb']}KB（建议历史段归档拆分）")
    for rel in live:
        if not rel.startswith("wiki/projects/"):
            continue
        n, inside = 0, False
        for line in wiki[rel].splitlines():
            if line.startswith("#"):
                inside = any(h in line for h in DECISION_HEADS)
                continue
            if inside and re.match(r"\s*- ", line):
                n += 1
        if n > cfg["decision_log_max"]:
            items.append(f"膨胀: {rel} 决策日志 {n} 条 > {cfg['decision_log_max']}（建议老条目归档）")

    # 5. TODO 年龄（开放任务按分档计数；无日期 token 的无法测龄跳过；
    #    已带 #todo/stale 标记 = maintain 已分诊过的僵尸，跳过防止体检永不归零）
    todo_text = wiki.get("wiki/todos.md", "")
    token_date_re = re.compile(r"[➕📅⏳🛫]\s*(\d{4}-\d{2}-\d{2})")
    aged = []
    for line in todo_text.splitlines():
        m = re.match(r"^\s*- \[ \] (.+)$", line)
        if not m or "#todo/stale" in line:
            continue
        dates = [d for d in (_to_date(x) for x in token_date_re.findall(m.group(1))) if d]
        if dates:
            aged.append(((today - min(dates)).days, m.group(1).strip()))
    remaining = aged
    for bound in sorted(cfg["todo_stale_days"], reverse=True):
        hit = [(a, s) for a, s in remaining if a > bound]
        remaining = [(a, s) for a, s in remaining if a <= bound]
        if hit:
            oldest = max(hit)
            items.append(f"TODO 年龄: 超 {bound} 天未完成 {len(hit)} 条（最老 {oldest[0]} 天：{oldest[1][:40]}）")

    for it in items:
        print(f"🩺 {it}")
    print("----")
    tail = "（说「维护 vault」处理；阈值可在 worklog.config.yaml 的 maintenance 段调整）" if items else ""
    print(f"🩺 {len(items)} 项待维护{tail}")
    return 2 if items else 0


if __name__ == "__main__":
    _vault, _health, _today = parse_argv(sys.argv)
    _root = _vault or default_root()
    sys.exit(run_health(_root, _today) if _health else main(_root))
