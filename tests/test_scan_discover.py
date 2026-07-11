"""CLI 级测试：scan.sh 与 discover.sh 的发现行为与行协议（fixture git 仓实测）。

这两个脚本是全系统的数据采集地基（discover 每次 init 跑、scan 每晚 ingest 跑），
CI 的 bash -n / shellcheck 只保证语法，行为回归靠本文件。
"""
import os
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCAN = ROOT / ".claude/skills/worklog-ingest/scripts/scan.sh"
DISCOVER = ROOT / ".claude/skills/worklog-init/scripts/discover.sh"

COMMIT_DATE = "2026-07-11T12:00:00+08:00"
SINCE = "2026-07-11T00:00:00+08:00"
UNTIL = "2026-07-11T23:59:59+08:00"


def sh(script, *args):
    return subprocess.run(["bash", str(script)] + [str(a) for a in args],
                          capture_output=True, text=True)


def make_repo(path, author="Test User", email="t@example.com", commit=True):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True, capture_output=True)
    if commit:
        (path / "f.txt").write_text("x", encoding="utf-8")
        env = {**os.environ,
               "GIT_AUTHOR_NAME": author, "GIT_AUTHOR_EMAIL": email,
               "GIT_COMMITTER_NAME": author, "GIT_COMMITTER_EMAIL": email,
               "GIT_AUTHOR_DATE": COMMIT_DATE, "GIT_COMMITTER_DATE": COMMIT_DATE}
        subprocess.run(["git", "-C", str(path), "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", "work"],
                       check=True, capture_output=True, env=env)
    return path


def test_discover_finds_nested_repo(tmp_path):
    make_repo(tmp_path / "cat" / "proj", commit=False)
    r = sh(DISCOVER, tmp_path)
    assert r.returncode == 0
    assert f"PROJECT {tmp_path}/cat/proj" in r.stdout


def test_discover_worklogignore_wins(tmp_path):
    p = make_repo(tmp_path / "secret", commit=False)
    (p / ".worklogignore").write_text("", encoding="utf-8")
    r = sh(DISCOVER, tmp_path)
    assert f"IGNORED {p}" in r.stdout
    assert f"PROJECT {p}" not in r.stdout


def test_discover_prunes_node_modules(tmp_path):
    make_repo(tmp_path / "app", commit=False)
    make_repo(tmp_path / "app" / "node_modules" / "dep", commit=False)
    r = sh(DISCOVER, tmp_path)
    assert f"PROJECT {tmp_path}/app" in r.stdout
    assert "node_modules" not in r.stdout


def test_discover_symlink_root(tmp_path):
    # 回归：root 是符号链接时曾静默零输出（[ -d ] 跟随符号链接而 find 默认 -P 不跟随，修复 = find -H）
    make_repo(tmp_path / "real" / "proj", commit=False)
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "real")
    r = sh(DISCOVER, link)
    assert "PROJECT" in r.stdout and "/proj" in r.stdout


def test_scan_commit_in_window(tmp_path):
    p = make_repo(tmp_path / "proj")
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path)
    assert r.returncode == 0
    assert f"REPO {p}" in r.stdout
    assert "COMMIT " in r.stdout and "|Test User|work" in r.stdout


def test_scan_author_filter_spaced_name(tmp_path):
    # 回归：--authors 含空格的名字曾因 word-splitting 静默丢全部 commit（修复 = 数组化）
    make_repo(tmp_path / "proj", author="Ann B Example", email="ann@example.com")
    hit = sh(SCAN, "--since", SINCE, "--until", UNTIL, "--authors", "Ann B Example", tmp_path)
    assert "COMMIT " in hit.stdout
    miss = sh(SCAN, "--since", SINCE, "--until", UNTIL, "--authors", "Nobody Else", tmp_path)
    assert "COMMIT " not in miss.stdout and "REPO " in miss.stdout


def test_scan_symlink_root(tmp_path):
    # 回归：同 discover，scan 的 root 为符号链接时曾静默零输出
    make_repo(tmp_path / "real" / "proj")
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "real")
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, link)
    assert "REPO " in r.stdout and "COMMIT " in r.stdout
