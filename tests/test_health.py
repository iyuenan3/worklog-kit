"""lint.py --health 健康节的 fixture 级测试（五项指标 + 静默路径 + config 阈值 + 排除规则）。

退出码契约：0 = 健康 / 2 = 有待维护项（1 保留给正误节 must-fix）。
全部用 --today 固定「今天」，测试不依赖真实时钟与时区。
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LINT = ROOT / ".claude/skills/worklog-lint/scripts/lint.py"
TODAY = "2026-07-12"


def run_health(vault, *args):
    return subprocess.run(
        [sys.executable, str(LINT), "--health", "--vault", str(vault), "--today", TODAY]
        + [str(a) for a in args],
        capture_output=True, text=True,
    )


def make_vault(tmp_path, maintenance_yaml=""):
    """最小健康 vault：契约骨架齐全、零腐坏。"""
    (tmp_path / "diaries").mkdir()
    (tmp_path / "wiki" / "projects").mkdir(parents=True)
    (tmp_path / "wiki" / "index.md").write_text(
        "# index\n\n## 最后更新\n\n## 项目\n\n## 日记\n", encoding="utf-8")
    (tmp_path / "wiki" / "log.md").write_text(
        "# log\n<!-- ingest:log-anchor -->\n", encoding="utf-8")
    (tmp_path / "wiki" / "todos.md").write_text(
        "# TODO\n\n## 进行中\n\n## 待办\n", encoding="utf-8")
    cfg = "schema_version: 1\ntimezone: Asia/Shanghai\nlanguage: zh\n"
    if maintenance_yaml:
        cfg += maintenance_yaml
    (tmp_path / "worklog.config.yaml").write_text(cfg, encoding="utf-8")
    return tmp_path


def add_diary(vault, date, body):
    (vault / "diaries" / f"{date}.md").write_text(
        f"---\ndate: {date}\n---\n{body}\n", encoding="utf-8")


def add_project(vault, slug, last_updated, body=""):
    (vault / "wiki" / "projects" / f"{slug}.md").write_text(
        f"---\nlast_updated: {last_updated}\nsource_count: 1\ndiaries: []\n---\n# {slug}\n{body}\n",
        encoding="utf-8")


def test_healthy_vault_silent(tmp_path):
    v = make_vault(tmp_path)
    add_diary(v, "2026-07-11", "提及 [[alpha]]。")
    add_project(v, "alpha", "2026-07-11")
    r = run_health(v)
    assert r.returncode == 0
    assert "🩺 0 项待维护" in r.stdout


def test_drift_detected(tmp_path):
    v = make_vault(tmp_path)
    add_project(v, "alpha", "2026-05-01")
    add_diary(v, "2026-07-10", "今天推进 [[alpha]]。")
    r = run_health(v)
    assert r.returncode == 2
    assert "状态漂移" in r.stdout and "alpha" in r.stdout


def test_drift_within_threshold_silent(tmp_path):
    v = make_vault(tmp_path)
    add_project(v, "alpha", "2026-07-01")
    add_diary(v, "2026-07-10", "今天推进 [[alpha]]。")
    assert run_health(v).returncode == 0


def test_orphan_detected_and_structural_excluded(tmp_path):
    v = make_vault(tmp_path)
    (v / "wiki" / "notes.md").write_text("# 旧笔记，无人引用\n", encoding="utf-8")
    r = run_health(v)
    assert r.returncode == 2
    assert "孤儿页: wiki/notes.md" in r.stdout
    # 契约骨架（index / log / todos）不算孤儿
    assert "index.md" not in r.stdout and "todos.md" not in r.stdout


def test_orphan_rescued_by_inbound_link(tmp_path):
    v = make_vault(tmp_path)
    (v / "wiki" / "notes.md").write_text("# 笔记\n", encoding="utf-8")
    add_project(v, "alpha", TODAY, "相关：[[notes]]")
    add_diary(v, "2026-07-11", "推进 [[alpha]]。")
    r = run_health(v)
    assert "孤儿页" not in r.stdout


def test_entity_split_detected(tmp_path):
    v = make_vault(tmp_path)
    add_project(v, "chat-api", TODAY)
    add_diary(v, "2026-07-10", "改了 [[chat-api]]，另一处写成 [[Chat API]]。")
    r = run_health(v)
    assert r.returncode == 2
    assert "实体分裂候选" in r.stdout and "Chat API" in r.stdout


def test_alias_stub_suppresses_split(tmp_path):
    v = make_vault(tmp_path)
    add_project(v, "chat-api", TODAY)
    (v / "wiki" / "Chat API.md").write_text(
        "---\nalias_of: chat-api\n---\n→ [[chat-api]]\n", encoding="utf-8")
    add_diary(v, "2026-07-10", "改了 [[chat-api]]，旧日记写法 [[Chat API]]。")
    r = run_health(v)
    assert "实体分裂候选" not in r.stdout


def test_bloat_size_and_decision_log(tmp_path):
    v = make_vault(tmp_path, "maintenance:\n  bloat_kb: 1\n  decision_log_max: 3\n")
    decisions = "\n".join(f"- 2026-06-{i:02d} 决策 {i}" for i in range(1, 6))
    add_project(v, "alpha", TODAY, "## 决策日志\n" + decisions + "\n\nx" * 1200)
    add_diary(v, "2026-07-11", "推进 [[alpha]]。")
    r = run_health(v)
    assert r.returncode == 2
    assert "膨胀" in r.stdout
    assert "决策日志 5 条 > 3" in r.stdout
    assert "KB" in r.stdout


def test_todo_age_buckets(tmp_path):
    v = make_vault(tmp_path)
    (v / "wiki" / "todos.md").write_text(
        "# TODO\n\n## 进行中\n\n- [ ] 很老的任务 ➕ 2026-01-01\n"
        "- [ ] 有点老的任务 📅 2026-06-01\n"
        "- [ ] 新任务 ➕ 2026-07-10\n"
        "- [x] 已完成的老任务 ➕ 2026-01-01\n\n## 待办\n", encoding="utf-8")
    r = run_health(v)
    assert r.returncode == 2
    assert "超 90 天未完成 1 条" in r.stdout
    assert "超 30 天未完成 1 条" in r.stdout


def test_todo_stale_marked_skipped(tmp_path):
    v = make_vault(tmp_path)
    (v / "wiki" / "todos.md").write_text(
        "# TODO\n\n## 进行中\n\n- [ ] 已分诊的僵尸 #todo/stale ➕ 2026-01-01\n\n## 待办\n",
        encoding="utf-8")
    # maintain 已标记的僵尸不再重复报（防体检永不归零），红线「不关闭」不变
    assert run_health(v).returncode == 0


def test_config_threshold_override(tmp_path):
    v = make_vault(tmp_path, "maintenance:\n  drift_days: 100\n")
    add_project(v, "alpha", "2026-05-01")
    add_diary(v, "2026-07-10", "推进 [[alpha]]。")
    # 默认 14 天会报；阈值放宽到 100 天后静默
    assert run_health(v).returncode == 0


def test_archive_excluded(tmp_path):
    v = make_vault(tmp_path)
    (v / "wiki" / "archive").mkdir()
    (v / "wiki" / "archive" / "old-page.md").write_text("# 已归档\n", encoding="utf-8")
    r = run_health(v)
    assert "孤儿页" not in r.stdout
    assert r.returncode == 0
