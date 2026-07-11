"""CLI 级测试：三个校验脚本的退出码契约（0 = 干净 / 1 = 有命中）。"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PUNCT = ROOT / ".claude/skills/worklog-ingest/scripts/punctuation_check.py"
DATE = ROOT / ".claude/skills/worklog-ingest/scripts/date_weekday_check.py"
LINT = ROOT / ".claude/skills/worklog-lint/scripts/lint.py"


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(script)] + [str(a) for a in args],
        capture_output=True, text=True,
    )


def test_punct_clean_chinese(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("这是干净的中文，标点正确。\n", encoding="utf-8")
    assert run(PUNCT, f).returncode == 0


def test_punct_halfwidth_comma_in_cjk(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("这里有半角逗号,在中文里。\n", encoding="utf-8")
    r = run(PUNCT, f)
    assert r.returncode == 1
    assert "半角" in r.stdout


def test_punct_emdash(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("这句话——用了破折号。\n", encoding="utf-8")
    assert run(PUNCT, f).returncode == 1


def test_punct_ascii_only_passes(tmp_path):
    f = tmp_path / "a.md"
    f.write_text("pure english text, with commas and (parens). fine.\n", encoding="utf-8")
    assert run(PUNCT, f).returncode == 0


def test_date_weekday_ok(tmp_path):
    f = tmp_path / "d.md"
    f.write_text("---\ndate: 2026-07-11\nday: 周六\n---\n# 2026年7月11日（周六）\n", encoding="utf-8")
    assert run(DATE, f).returncode == 0


def test_date_weekday_mismatch(tmp_path):
    f = tmp_path / "d.md"
    f.write_text("---\ndate: 2026-07-11\nday: 周日\n---\n", encoding="utf-8")
    r = run(DATE, f)
    assert r.returncode == 1
    assert "周六" in r.stdout


def _mk_vault(tmp_path):
    (tmp_path / "wiki" / "projects").mkdir(parents=True)
    (tmp_path / "diaries").mkdir()
    (tmp_path / "wiki" / "index.md").write_text(
        "# Wiki 索引\n## 最后更新\n## 项目\n## 日记\n", encoding="utf-8")
    (tmp_path / "wiki" / "log.md").write_text(
        "<!-- ingest:log-anchor -->\n", encoding="utf-8")
    (tmp_path / "wiki" / "todos.md").write_text(
        "## 进行中\n## 待办\n", encoding="utf-8")


def test_lint_clean_vault(tmp_path):
    _mk_vault(tmp_path)
    (tmp_path / "diaries" / "2026-07-10.md").write_text(
        "---\ndate: 2026-07-10\n---\nok\n", encoding="utf-8")
    r = run(LINT, "--vault", tmp_path)
    assert r.returncode == 0


def test_lint_catches_secret_and_missing_frontmatter(tmp_path):
    _mk_vault(tmp_path)
    (tmp_path / "diaries" / "2026-07-11.md").write_text(
        'no frontmatter\napi_key = "abcdef1234567890abcdef"\n', encoding="utf-8")
    r = run(LINT, "--vault", tmp_path)
    assert r.returncode == 1
    assert "凭证" in r.stdout
    assert "frontmatter" in r.stdout


def test_lint_missing_anchor_is_hard(tmp_path):
    _mk_vault(tmp_path)
    (tmp_path / "wiki" / "index.md").write_text("# 被用户改坏的 index\n", encoding="utf-8")
    assert run(LINT, "--vault", tmp_path).returncode == 1


def test_lint_conflict_copy_is_soft(tmp_path):
    # Obsidian 同步冲突副本等非日记命名文件不该把 lint 卡成红
    _mk_vault(tmp_path)
    (tmp_path / "diaries" / "2026-07-10 conflicted copy.md").write_text(
        "no frontmatter\n", encoding="utf-8")
    r = run(LINT, "--vault", tmp_path)
    assert r.returncode == 0
    assert "非日记命名" in r.stdout


def test_lint_ignore_comment_suppresses_secret(tmp_path):
    _mk_vault(tmp_path)
    (tmp_path / "diaries" / "2026-07-12.md").write_text(
        '---\ndate: 2026-07-12\n---\n示例：api_key = "abcdef1234567890abcdef" <!-- lint:ignore -->\n',
        encoding="utf-8")
    r = run(LINT, "--vault", tmp_path)
    assert r.returncode == 0
    assert "凭证" not in r.stdout


def test_lint_codespan_wikilink_not_broken_link(tmp_path):
    _mk_vault(tmp_path)
    (tmp_path / "wiki" / "todos.md").write_text(
        "## 进行中\n## 待办\n> 语法：`- [ ] 描述 [[关联页]]`\n", encoding="utf-8")
    r = run(LINT, "--vault", tmp_path)
    assert "断链" not in r.stdout
