"""CLI 级测试：scan.sh 与 discover.sh 的发现行为与行协议（fixture git 仓实测）。

这两个脚本是全系统的数据采集地基（discover 每次 init 跑、scan 每晚 ingest 跑），
CI 的 bash -n / shellcheck 只保证语法，行为回归靠本文件。
"""
import os
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCAN = ROOT / ".claude/skills/worklog-ingest/scripts/scan.sh"
DISCOVER = ROOT / ".claude/skills/worklog-init/scripts/discover.sh"
GHSCAN = ROOT / ".claude/skills/worklog-ingest/scripts/github-scan.sh"
BASH = shutil.which("bash")

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


def test_scan_unmounted_root_is_skip_not_error(tmp_path):
    # 「每个数据源都可失败」核心承诺：root 不存在（硬盘未挂载）= 常态路径，stderr 提示 + exit 0
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path / "not-mounted")
    assert r.returncode == 0
    assert "SKIP_UNMOUNTED" in r.stderr
    assert r.stdout.strip() == ""


def test_discover_unmounted_root_is_skip_not_error(tmp_path):
    r = sh(DISCOVER, tmp_path / "not-mounted")
    assert r.returncode == 0
    assert "SKIP_UNMOUNTED" in r.stderr


def test_github_scan_no_gh_exit_4(tmp_path):
    empty = tmp_path / "emptybin"
    empty.mkdir()
    r = subprocess.run([BASH, str(GHSCAN), "--since-utc", "2026-07-11T00:00:00Z",
                        "--until-utc", "2026-07-11T23:59:59Z"],
                       capture_output=True, text=True,
                       env={"PATH": str(empty), "LC_ALL": "C"})
    assert r.returncode == 4
    assert "NO_GH" in r.stderr


def test_scan_symlink_root(tmp_path):
    # 回归：同 discover，scan 的 root 为符号链接时曾静默零输出
    make_repo(tmp_path / "real" / "proj")
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "real")
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, link)
    assert "REPO " in r.stdout and "COMMIT " in r.stdout


def _commit_env(author="Test User", email="t@example.com"):
    return {**os.environ,
            "GIT_AUTHOR_NAME": author, "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": author, "GIT_COMMITTER_EMAIL": email,
            "GIT_AUTHOR_DATE": COMMIT_DATE, "GIT_COMMITTER_DATE": COMMIT_DATE}


def _repo_block(stdout, repo_path):
    """取指定仓的 REPO 段（到下一个 REPO 行为止）。"""
    for block in stdout.split("REPO "):
        if block.startswith(f"{repo_path}\n"):
            return block
    raise AssertionError(f"no REPO block for {repo_path}\n{stdout}")


def test_scan_nested_repo_phantom_dirty_filtered(tmp_path):
    # 回归：嵌套子仓（含隔一层目录的 sub/child 形态）曾让干净父仓永久 DIRTY≥1（?? sub/ 结构幻影），
    # presence 级父仓永远到不了「无信号可省略」；子仓自身仍独立成段、commit 不漏
    parent = make_repo(tmp_path / "parent")
    child = make_repo(parent / "sub" / "child")
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path)
    assert "DIRTY 0" in _repo_block(r.stdout, parent)
    assert "COMMIT " in _repo_block(r.stdout, child)


def test_scan_nested_repo_real_untracked_still_counts(tmp_path):
    # 幻影过滤不能吞掉真实未追踪文件：父仓有真 untracked 时照常计
    parent = make_repo(tmp_path / "parent")
    make_repo(parent / "nested", commit=False)
    (parent / "real.txt").write_text("x", encoding="utf-8")
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path)
    assert "DIRTY 1" in _repo_block(r.stdout, parent)


def test_scan_submodule_discovered_and_scanned(tmp_path):
    # 回归：submodule 的 .git 是 gitdir: 指针文件，曾是发现与扫描双盲区（内部 commit 整天消失）
    src = make_repo(tmp_path / "srcrepo")
    main = make_repo(tmp_path / "root" / "main")
    env = _commit_env()
    subprocess.run(["git", "-C", str(main), "-c", "protocol.file.allow=always",
                    "submodule", "add", str(src), "sub"],
                   check=True, capture_output=True, env=env)
    (main / "sub" / "s2.txt").write_text("y", encoding="utf-8")
    subprocess.run(["git", "-C", str(main / "sub"), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(main / "sub"), "commit", "-q", "-m", "sub inner work"],
                   check=True, capture_output=True, env=env)
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path / "root")
    assert "sub inner work" in _repo_block(r.stdout, main / "sub")
    d = sh(DISCOVER, tmp_path / "root")
    assert f"PROJECT {main / 'sub'}" in d.stdout


def test_scan_worktree_skip_no_duplicate(tmp_path):
    # worktree 与主仓共享 refs：不独立成段（防 COMMIT 重复计），stderr 出 WORKTREE_SKIP 信号
    # 且信号自带主仓路径（消费方据此机械比对 REPO / IGNORED 行）；worktree 内 commit 经主仓捕获
    main = make_repo(tmp_path / "main")
    wt = tmp_path / "wt"
    subprocess.run(["git", "-C", str(main), "worktree", "add", "-q", "-b", "feat", str(wt)],
                   check=True, capture_output=True)
    (wt / "wf.txt").write_text("z", encoding="utf-8")
    subprocess.run(["git", "-C", str(wt), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(wt), "commit", "-q", "-m", "feat work in worktree"],
                   check=True, capture_output=True, env=_commit_env())
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path)
    assert f"WORKTREE_SKIP {wt} -> {main.resolve()}" in r.stderr
    assert r.stdout.count("REPO ") == 1
    assert r.stdout.count("feat work in worktree") == 1
    d = sh(DISCOVER, tmp_path)
    assert f"WORKTREE_SKIP {wt} -> {main.resolve()}" in d.stderr
    assert f"PROJECT {wt}" not in d.stdout


def test_scan_sepgitdir_named_worktrees_not_skipped(tmp_path):
    # 回归：worktree 判据曾用 gitdir 路径子串匹配 /worktrees/，把「--separate-git-dir 到名含
    # worktrees 的目录」这类独立对象库误判成 worktree，commit 静默丢失；语义判据不受路径名影响
    store = tmp_path / "worktrees" / "store"
    work = tmp_path / "root" / "trap"
    store.parent.mkdir(parents=True)
    work.parent.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", f"--separate-git-dir={store}", str(work)],
                   check=True, capture_output=True)
    (work / "x.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "-C", str(work), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "trap work"],
                   check=True, capture_output=True, env=_commit_env())
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path / "root")
    assert "trap work" in _repo_block(r.stdout, work)
    assert "WORKTREE_SKIP" not in r.stderr


def test_scan_dirty_phantom_filter_space_and_unicode_names(tmp_path):
    # 回归：porcelain 对含空格 / 非 ASCII 的路径加引号，`?? <dir>/` 模式匹配不到，
    # 幻影过滤对最常见命名（macOS 空格目录、中文目录）失效；-z 解析后应一并生效
    parent = make_repo(tmp_path / "parent")
    make_repo(parent / "my repo", commit=False)
    make_repo(parent / "中文仓", commit=False)
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path)
    assert "DIRTY 0" in _repo_block(r.stdout, parent)


def test_scan_dirty_untracked_dir_with_file_counts(tmp_path):
    # 幻影过滤的反向面：含真实文件的普通未追踪目录必须计入（整目录级过滤回归的防线）
    parent = make_repo(tmp_path / "parent")
    (parent / "docs").mkdir()
    (parent / "docs" / "note.md").write_text("n", encoding="utf-8")
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path)
    assert "DIRTY 1" in _repo_block(r.stdout, parent)


def test_scan_dirty_symlink_only_dir_counts(tmp_path):
    # 回归：幻影判据曾只认 -type f，「只含符号链接的未追踪目录」被误当结构幻影归零；
    # symlink 是 git 一等追踪对象，算真实内容
    repo = make_repo(tmp_path / "proj")
    (repo / "links").mkdir()
    (repo / "links" / "hosts").symlink_to("/etc/hosts")
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path)
    assert "DIRTY 1" in _repo_block(r.stdout, repo)


def test_scan_dirty_rename_counts_once(tmp_path):
    # -z 下 rename 是「新路径 NUL 旧路径」双段记录，须多吞一段防双计
    repo = make_repo(tmp_path / "proj")
    subprocess.run(["git", "-C", str(repo), "mv", "f.txt", "g.txt"],
                   check=True, capture_output=True)
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path)
    assert "DIRTY 1" in _repo_block(r.stdout, repo)


def test_scan_stray_gitfile_skipped(tmp_path):
    # 恰好叫 .git 的杂文件（非 gitdir: 指针）不产出 REPO / PROJECT 块，防幻影条目污染行协议
    make_repo(tmp_path / "real")
    junk = tmp_path / "junk"
    junk.mkdir()
    (junk / ".git").write_text("not a pointer\n", encoding="utf-8")
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path)
    assert f"REPO {junk}" not in r.stdout
    d = sh(DISCOVER, tmp_path)
    assert f"PROJECT {junk}" not in d.stdout


def test_worklogignore_vetoes_subtree(tmp_path):
    # 否决权升级为子树否决：树顶一个 .worklogignore 罩住嵌套子仓（scan 与 discover 同一纪律），
    # 被否决子仓的 commit 零出现
    parent = make_repo(tmp_path / "sec")
    (parent / ".worklogignore").write_text("", encoding="utf-8")
    inner = make_repo(parent / "inner")
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path)
    assert f"IGNORED {inner}" in r.stdout
    assert f"REPO {inner}" not in r.stdout and "COMMIT " not in r.stdout
    d = sh(DISCOVER, tmp_path)
    assert f"IGNORED {inner}" in d.stdout
    assert f"PROJECT {inner}" not in d.stdout


def test_scan_worktree_of_ignored_main_is_silent(tmp_path):
    # 主仓被 .worklogignore 否决时，其 worktree 连 WORKTREE_SKIP 都不出（防被排除项目的路径泄漏）
    main = make_repo(tmp_path / "secret")
    (main / ".worklogignore").write_text("", encoding="utf-8")
    wt = tmp_path / "secwt"
    subprocess.run(["git", "-C", str(main), "worktree", "add", "-q", "-b", "f2", str(wt)],
                   check=True, capture_output=True)
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path)
    assert "WORKTREE_SKIP" not in r.stderr
    assert f"IGNORED {main}" in r.stdout


def test_scan_bad_depth_exit_2(tmp_path):
    # 非数字深度曾让 find 静默零输出（与「真没活动」不可区分），须前置校验报错
    make_repo(tmp_path / "proj")
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, "--depth", "banana", tmp_path)
    assert r.returncode == 2 and "Bad --depth" in r.stderr
    d = subprocess.run(["bash", str(DISCOVER), str(tmp_path)],
                       capture_output=True, text=True,
                       env={**os.environ, "WORKLOG_DISCOVER_DEPTH": "banana"})
    assert d.returncode == 2 and "Bad WORKLOG_DISCOVER_DEPTH" in d.stderr


def test_scan_degraded_tmpdir_worktree_still_skipped(tmp_path):
    # 降级路径（TMPDIR 不可写 → 退回逐 root 处理）也必须保持 worktree 分类纪律
    main = make_repo(tmp_path / "main")
    wt = tmp_path / "wt"
    subprocess.run(["git", "-C", str(main), "worktree", "add", "-q", "-b", "feat", str(wt)],
                   check=True, capture_output=True)
    r = subprocess.run(["bash", str(SCAN), "--since", SINCE, "--until", UNTIL, str(tmp_path)],
                       capture_output=True, text=True,
                       env={**os.environ, "TMPDIR": "/nonexistent-worklog-test"})
    assert f"WORKTREE_SKIP {wt} -> {main.resolve()}" in r.stderr
    assert r.stdout.count("REPO ") == 1


def test_scan_separate_git_dir_scanned(tmp_path):
    # --separate-git-dir 形态（.git 文件但非 worktree）是独立对象库，照常扫
    work = tmp_path / "work"
    subprocess.run(["git", "init", "-q", f"--separate-git-dir={tmp_path / 'store'}", str(work)],
                   check=True, capture_output=True)
    (work / "f.txt").write_text("x", encoding="utf-8")
    subprocess.run(["git", "-C", str(work), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "sepdir work"],
                   check=True, capture_output=True, env=_commit_env())
    r = sh(SCAN, "--since", SINCE, "--until", UNTIL, tmp_path)
    assert "sepdir work" in _repo_block(r.stdout, work)


def test_scan_mtime_ignores_nested_and_hidden(tmp_path):
    # 回归：MTIME 兜底曾被嵌套子仓与隐藏文件（.DS_Store）串扰成父仓假活动信号
    repo = make_repo(tmp_path / "proj")
    inner = make_repo(repo / "inner", commit=False)
    (inner / "i.txt").write_text("i", encoding="utf-8")
    (repo / ".DS_Store").write_text("", encoding="utf-8")
    subprocess.run(["touch", "-t", "202601011200", str(repo / "f.txt")], check=True)
    subprocess.run(["touch", "-t", "202607121500", str(inner / "i.txt"), str(repo / ".DS_Store")],
                   check=True)
    args = ["--since", "2026-07-12T00:00:00+08:00", "--until", "2026-07-12T23:59:59+08:00",
            "--touch-since", "202607120000"]
    r = sh(SCAN, *args, tmp_path)
    assert "MTIME_ACTIVE" not in _repo_block(r.stdout, repo)
    # 真实新文件仍触发
    (repo / "new.txt").write_text("n", encoding="utf-8")
    subprocess.run(["touch", "-t", "202607121500", str(repo / "new.txt")], check=True)
    r2 = sh(SCAN, *args, tmp_path)
    assert "MTIME_ACTIVE" in _repo_block(r2.stdout, repo)
