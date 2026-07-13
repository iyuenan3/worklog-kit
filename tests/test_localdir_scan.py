"""CLI 级测试：localdir-scan.sh（local-dir 源的 mtime 活动判定，presence 级信号）。

关键回归：窗口必须有上界（只有下界时「补充昨天 / 回填 N 天」必错账）、
噪音（.DS_Store / node_modules / 隐藏目录）不算活动、config 字面 ~ 的兜底展开。
"""
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOCALDIR = ROOT / ".claude/skills/worklog-ingest/scripts/localdir-scan.sh"

# 目标日 2026-07-10 的窗口（day_boundary 07:00，止减 1 秒保半开语义）
FROM = "202607100700"
TO = "202607110659.59"


def sh(*args, env=None):
    return subprocess.run(["bash", str(LOCALDIR)] + [str(a) for a in args],
                          capture_output=True, text=True, env=env)


def touch_t(stamp, *paths):
    subprocess.run(["touch", "-t", stamp] + [str(p) for p in paths], check=True)


def test_active_within_window(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("x", encoding="utf-8")
    touch_t("202607101200", f)
    r = sh("--from", FROM, "--to", TO, tmp_path)
    assert r.returncode == 0
    assert f"LOCALDIR {tmp_path}" in r.stdout
    assert "MTIME_ACTIVE" in r.stdout


def test_window_upper_bound(tmp_path):
    # 回归：目录在目标日之后动过（哪怕就是今天）不能把目标日记成有活动
    f = tmp_path / "doc.md"
    f.write_text("x", encoding="utf-8")
    touch_t("202607121500", f)
    r = sh("--from", FROM, "--to", TO, tmp_path)
    assert f"LOCALDIR {tmp_path}" in r.stdout
    assert "MTIME_ACTIVE" not in r.stdout


def test_window_lower_bound(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("x", encoding="utf-8")
    touch_t("202607011200", f)
    r = sh("--from", FROM, "--to", TO, tmp_path)
    assert "MTIME_ACTIVE" not in r.stdout


def test_noise_is_not_activity(tmp_path):
    # Finder 元数据 / 依赖安装 / 隐藏缓存不该被记成「今天动过这个项目」
    (tmp_path / "node_modules" / "dep").mkdir(parents=True)
    (tmp_path / ".cache").mkdir()
    for f in [tmp_path / ".DS_Store", tmp_path / "node_modules" / "dep" / "x.js",
              tmp_path / ".cache" / "c.bin"]:
        f.write_text("", encoding="utf-8")
        touch_t("202607101200", f)
    r = sh("--from", FROM, "--to", TO, tmp_path)
    assert f"LOCALDIR {tmp_path}" in r.stdout
    assert "MTIME_ACTIVE" not in r.stdout


def test_depth_cap(tmp_path):
    deep = tmp_path / "a" / "b" / "c" / "d"
    deep.mkdir(parents=True)
    f = deep / "deep.md"          # 深度 5 > 默认 4
    f.write_text("x", encoding="utf-8")
    touch_t("202607101200", f)
    assert "MTIME_ACTIVE" not in sh("--from", FROM, "--to", TO, tmp_path).stdout
    assert "MTIME_ACTIVE" in sh("--from", FROM, "--to", TO, "--depth", 5, tmp_path).stdout


def test_missing_path_is_skip_not_error(tmp_path):
    r = sh("--from", FROM, "--to", TO, tmp_path / "nope")
    assert r.returncode == 0
    assert "SKIP_MISSING" in r.stderr
    assert "LOCALDIR" not in r.stdout


def test_tilde_expansion(tmp_path):
    # 回归：config 原样传来的字面 "~/writing" 曾被误报成路径不存在
    d = tmp_path / "writing"
    d.mkdir()
    f = d / "doc.md"
    f.write_text("x", encoding="utf-8")
    touch_t("202607101200", f)
    env = {**os.environ, "HOME": str(tmp_path)}
    r = sh("--from", FROM, "--to", TO, "~/writing", env=env)
    assert "SKIP_MISSING" not in r.stderr
    assert "MTIME_ACTIVE" in r.stdout


def test_bad_time_args_exit_2(tmp_path):
    r = sh("--from", "banana", "--to", TO, tmp_path)
    assert r.returncode == 2
    assert "Bad --from/--to" in r.stderr


def test_bad_depth_exit_2(tmp_path):
    r = sh("--from", FROM, "--to", TO, "--depth", "banana", tmp_path)
    assert r.returncode == 2
    assert "Bad --depth" in r.stderr


def test_multi_path_mixed_missing_and_active(tmp_path):
    # SKILL 规定多条 local-dir 源合并一次调用：首个路径缺失不得让后续路径失去扫描
    d = tmp_path / "writing"
    d.mkdir()
    f = d / "doc.md"
    f.write_text("x", encoding="utf-8")
    touch_t("202607101200", f)
    r = sh("--from", FROM, "--to", TO, tmp_path / "nope", d)
    assert r.returncode == 0
    assert "SKIP_MISSING" in r.stderr
    assert f"LOCALDIR {d}" in r.stdout and "MTIME_ACTIVE" in r.stdout


def test_unwritable_tmpdir_distinct_error(tmp_path):
    # TMPDIR 不可写与时间格式错是两种故障，报错须可区分（否则自救方向全错）
    r = subprocess.run(["bash", str(LOCALDIR), "--from", FROM, "--to", TO, str(tmp_path)],
                       capture_output=True, text=True,
                       env={**os.environ, "TMPDIR": "/nonexistent-worklog-test"})
    assert r.returncode == 2
    assert "TMPDIR" in r.stderr and "Bad --from/--to" not in r.stderr
