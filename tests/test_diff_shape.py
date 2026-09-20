"""Tests for hooks/diff_shape.py. Run: python tests/test_diff_shape.py  (or pytest)."""
import importlib.util
import inspect
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "hooks" / "diff_shape.py"
_spec = importlib.util.spec_from_file_location("diff_shape", SCRIPT)
ds = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ds)


def diff(path, added, start=1):
    body = "\n".join("+" + l for l in added)
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -0,0 +{start},{len(added)} @@\n{body}\n"


def codes(result):
    return sorted(f["code"] for f in result["findings"])


def test_divider_forensic_and_shouting():
    src = ["# ── lifecycle ──", "# Measured 2026-09-12: six restarts, see PR #1508", "# FAILS CLOSED. keep", "x = 1"]
    r = ds.analyze_diff(diff("a.py", src))
    assert codes(r) == ["divider", "forensic-comment", "shouting"]
    assert not r["ok"]


def test_python_except_and_docstring_checks():
    source = (
        "def tiny(x):\n"
        '    """One.\n    Two.\n    Three.\n    Four.\n    """\n'
        "    return x\n\n"
        "def guarded():\n"
        "    try:\n        run()\n    except Exception:\n        pass\n"
        "    try:\n        run()\n    except ValueError:\n        log()\n"
    )
    lines = source.splitlines()
    r = ds.analyze_diff(diff("m.py", lines), blob_for=lambda p: source)
    assert codes(r) == ["docstring-over-body", "swallowed-except"]


def test_specific_except_pass_only_warns():
    source = "def f():\n    try:\n        run()\n    except OSError:\n        pass\n"
    r = ds.analyze_diff(diff("m.py", source.splitlines()), blob_for=lambda p: source)
    assert codes(r) == ["silent-except"] and r["ok"]


def test_unchanged_python_nodes_are_not_reported():
    source = "def old():\n    try:\n        run()\n    except Exception:\n        pass\n\nNEW = 1\n"
    r = ds.analyze_diff(diff("m.py", ["NEW = 1"], start=7), blob_for=lambda p: source)
    assert r["findings"] == []


def test_empty_catch_in_c_family():
    r = ds.analyze_diff(diff("a.ts", ["try {", "  go();", "} catch (e) {", "}"]))
    assert codes(r) == ["swallowed-except"]


def test_comment_share_thresholds():
    code = ["v%d = %d" % (i, i) for i in range(40)]
    r = ds.analyze_diff(diff("a.py", code + ["# note %d" % i for i in range(8)]))
    assert codes(r) == ["comment-share"] and r["findings"][0]["level"] == "warn"
    r = ds.analyze_diff(diff("a.py", code + ["# note %d" % i for i in range(20)]))
    assert r["findings"][0]["level"] == "fail"
    assert ds.analyze_diff(diff("a.py", code + ["# one"]))["findings"] == []


def test_large_commit_and_lockfiles_skipped():
    r = ds.analyze_diff("".join(diff(f"f{i}.py", ["x = 1"]) for i in range(9)))
    assert codes(r) == ["large-commit"]
    assert ds.analyze_diff(diff("package-lock.json", ["# " * 5] * 50))["findings"] == []


def test_commit_message_shape():
    good = "fix(auth): compare token expiry in UTC\n\nNaive local time drifted an hour at DST.\n\nClaude-Session: https://x\nCo-Authored-By: a <a@b>\n"
    r = ds.analyze_message(good)
    assert r["ok"] and r["body_lines"] == 1 and r["findings"] == []
    bad = "s" * 80 + "\n\nWHAT SHIPS.\n" + "line\n" * 9 + "Ran pytest: 300 passed\n"
    r = ds.analyze_message(bad)
    assert codes(r) == ["headed-section", "long-body", "long-subject", "transcript"] and not r["ok"]


def _git(*a, cwd):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout


def test_hooks_in_a_real_repo(tmp_path):
    if not shutil.which("git"):
        return
    repo = tmp_path / "r"
    repo.mkdir()
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "t@t", cwd=repo)
    _git("config", "user.name", "t", cwd=repo)
    (repo / "a.py").write_text("# ── section ──\ntry:\n    x = 1\nexcept Exception:\n    pass\n", "utf-8")
    _git("add", "a.py", cwd=repo)
    env = {**os.environ, "DIFF_SHAPE_DIR": str(tmp_path / "state")}
    warn = subprocess.run([sys.executable, str(SCRIPT), "pre-commit"], cwd=repo, env={**env, "DIFF_SHAPE_MODE": "warn"},
                          capture_output=True, text=True)
    assert warn.returncode == 0 and "divider" in warn.stderr and "swallowed-except" in warn.stderr
    block = subprocess.run([sys.executable, str(SCRIPT), "pre-commit"], cwd=repo, env={**env, "DIFF_SHAPE_MODE": "block"},
                           capture_output=True, text=True)
    assert block.returncode == 1 and "commit refused" in block.stderr
    msg = tmp_path / "MSG"
    msg.write_text("subject\n\nVERIFIED BY LOADING IT.\nbody\n", "utf-8")
    m = subprocess.run([sys.executable, str(SCRIPT), "commit-msg", str(msg)], cwd=repo, env={**env, "DIFF_SHAPE_MODE": "block"},
                       capture_output=True, text=True)
    assert m.returncode == 1 and "headed-section" in m.stderr
    _git("commit", "-q", "-m", "x", cwd=repo)
    scan = subprocess.run([sys.executable, str(SCRIPT), "scan"], cwd=repo, env=env, capture_output=True, text=True)
    assert scan.returncode == 0 and "divider" in scan.stderr and '"files": 1' in scan.stdout
    ins = subprocess.run([sys.executable, str(SCRIPT), "install", "--repo", str(repo)], capture_output=True, text=True, env=env)
    assert ins.returncode == 0, ins.stderr
    for name in ("pre-commit", "commit-msg"):
        assert "diff-shape" in (repo / ".git" / "hooks" / name).read_text("utf-8")
    rep = subprocess.run([sys.executable, str(SCRIPT), "report", "--json"], capture_output=True, text=True, env=env)
    assert '"diffs": 2' in rep.stdout


def test_hook_never_fails_outside_a_repo(tmp_path):
    env = {**os.environ, "DIFF_SHAPE_DIR": str(tmp_path)}
    proc = subprocess.run([sys.executable, str(SCRIPT), "pre-commit"], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert proc.returncode == 0


if __name__ == "__main__":
    failed = 0
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        try:
            if "tmp_path" in inspect.signature(fn).parameters:
                with tempfile.TemporaryDirectory() as d:
                    fn(Path(d))
            else:
                fn()
            print(f"PASS {name}")
        except Exception as exc:
            failed += 1
            print(f"FAIL {name}: {exc!r}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
