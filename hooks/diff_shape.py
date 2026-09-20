#!/usr/bin/env python3
"""Diff shape: measure the prose and the hazards in a staged diff and its commit message.

Git hooks (install per repo with `diff_shape.py install`):
  diff_shape.py pre-commit          reads `git diff --cached`, prints findings, logs one row
  diff_shape.py commit-msg <file>   checks the message shape
Tools:
  diff_shape.py measure [--msg] < diff_or_message
  diff_shape.py install [--repo DIR]
  diff_shape.py mode [off|warn|block]
  diff_shape.py report [--days N] [--json]
  diff_shape.py version

Stdlib only, Python 3.8+. warn mode (default) never fails a commit; block mode fails
only on `fail`-class findings. State: ~/.claude/diff_shape/ (DIFF_SHAPE_DIR). The log
stores counts, never code.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

__version__ = "3.0.0"  # must equal VERSION; tests/test_version_sync.py enforces it

MODES = ("off", "warn", "block")
DEFAULT_MODE = "warn"
LIMITS = {
    "comment_share_warn": 0.15,
    "comment_share_fail": 0.25,
    "min_added_for_share": 40,
    "docstring_lines": 3,
    "module_docstring_lines": 10,
    "commit_lines": 800,
    "commit_files": 8,
    "subject_chars": 72,
    "body_lines": 8,
}

_HASH_LANGS = {".py", ".sh", ".bash", ".ps1", ".psm1", ".yml", ".yaml", ".toml", ".rb", ".pl", ".r"}
_C_LANGS = {".js", ".jsx", ".mjs", ".ts", ".tsx", ".kt", ".kts", ".java", ".go", ".rs", ".c", ".h",
            ".cpp", ".hpp", ".cs", ".swift", ".scala", ".css", ".scss", ".php", ".dart"}
_SKIP = re.compile(r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Cargo\.lock|.*\.min\.(js|css)|vendor/|node_modules/|dist/|build/)")

_PUNCT = "-=─═*~_#/"
_DIVIDER_RE = re.compile(rf"^(?:[{_PUNCT}]{{6,}}|[{_PUNCT}]{{2,}}\s*[^{_PUNCT}]{{1,60}}?\s*[{_PUNCT}]{{2,}})\s*$")
_FORENSIC_RE = re.compile(r"\b20\d\d-\d\d-\d\d\b|(?<![\w/])#\d{2,}\b|\bPRs?\s*#?\d{2,}\b|\b(?:before|since|as of)\s+v?\d+\.\d+")
_SHOUT_RE = re.compile(r"\b[A-Z]{3,}(?:\s+[A-Z]{3,})+\b")
_EMPTY_CATCH_RE = re.compile(r"\bcatch\b\s*(?:\([^)]*\))?\s*\{\s*\}")
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def parse_diff(text: str) -> Tuple[Dict[str, List[Tuple[int, str]]], int]:
    """Return {path: [(new_lineno, added_line)]} and the count of removed lines."""
    files: Dict[str, List[Tuple[int, str]]] = {}
    path, lineno, removed = None, 0, 0
    for raw in text.splitlines():
        if raw.startswith("+++ "):
            name = raw[4:].strip()
            path = None if name == "/dev/null" else re.sub(r"^b/", "", name)
            if path is not None:
                files.setdefault(path, [])
            continue
        if raw.startswith("--- ") or raw.startswith("diff ") or raw.startswith("index ") or raw.startswith("Binary "):
            continue
        m = _HUNK_RE.match(raw)
        if m:
            lineno = int(m.group(1))
            continue
        if path is None:
            continue
        if raw.startswith("+"):
            files[path].append((lineno, raw[1:]))
            lineno += 1
        elif raw.startswith("-"):
            removed += 1
        elif raw.startswith("\\"):
            continue
        else:
            lineno += 1
    return files, removed


def _is_comment(line: str, ext: str) -> bool:
    s = line.strip()
    if ext in _HASH_LANGS:
        return s.startswith("#") and not s.startswith("#!")
    if ext in _C_LANGS:
        return s.startswith("//") or s.startswith("/*") or s.startswith("* ") or s == "*" or s.startswith("*/")
    return False


def _comment_body(line: str) -> str:
    return re.sub(r"^\s*(?:#+|//+|/\*+|\*+/?)\s?", "", line).strip()


def _finding(level: str, code: str, path: str, line: Optional[int], text: str) -> Dict[str, Any]:
    return {"level": level, "code": code, "path": path, "line": line, "text": text[:90]}


def _python_findings(path: str, source: str, added: Set[int]) -> Tuple[List[Dict[str, Any]], Set[int]]:
    """Findings from the staged Python file, restricted to nodes on added lines; plus docstring line numbers."""
    out: List[Dict[str, Any]] = []
    doc_lines: Set[int] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return out, doc_lines

    def docstring_span(node: ast.AST) -> Optional[Tuple[int, int]]:
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                and isinstance(body[0].value.value, str):
            return body[0].lineno, body[0].end_lineno or body[0].lineno
        return None

    span = docstring_span(tree)
    if span:
        doc_lines.update(range(span[0], span[1] + 1))
        n = span[1] - span[0] + 1
        if span[0] in added and n > LIMITS["module_docstring_lines"]:
            out.append(_finding("warn", "long-module-docstring", path, span[0], f"{n}-line module docstring"))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            span = docstring_span(node)
            if not span:
                continue
            doc_lines.update(range(span[0], span[1] + 1))
            if node.lineno not in added:
                continue
            ds = span[1] - span[0] + 1
            body = (node.end_lineno or span[1]) - span[1]
            if ds > LIMITS["docstring_lines"] and ds > body:
                out.append(_finding("warn", "docstring-over-body", path, node.lineno,
                                    f"{node.name}: {ds}-line docstring, {body}-line body"))
        elif isinstance(node, ast.ExceptHandler) and node.lineno in added:
            stmts = node.body
            trivial = all(isinstance(s, (ast.Pass, ast.Continue)) or
                          (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)) for s in stmts)
            broad = node.type is None or (isinstance(node.type, ast.Name) and node.type.id in ("Exception", "BaseException"))
            if trivial:
                out.append(_finding("fail", "swallowed-except", path, node.lineno, "handler body is only pass"))
            elif broad and not any(isinstance(s, ast.Raise) for s in ast.walk(node)):
                out.append(_finding("warn", "broad-except", path, node.lineno, "catch-all that never re-raises"))
    return out, doc_lines


def analyze_diff(text: str, blob_for: Callable[[str], Optional[str]] = lambda p: None) -> Dict[str, Any]:
    files, removed = parse_diff(text)
    findings: List[Dict[str, Any]] = []
    added_nonblank = comment_lines = added_total = 0
    for path, lines in files.items():
        if _SKIP.search(path):
            continue
        ext = Path(path).suffix.lower()
        added_total += len(lines)
        added_set = {n for n, _ in lines}
        doc_lines: Set[int] = set()
        if ext == ".py":
            source = blob_for(path)
            if source is not None:
                py, doc_lines = _python_findings(path, source, added_set)
                findings.extend(py)
        if ext in _C_LANGS:
            joined = "\n".join(l for _, l in lines)
            for m in _EMPTY_CATCH_RE.finditer(joined):
                at = lines[joined[:m.start()].count("\n")][0]
                findings.append(_finding("fail", "swallowed-except", path, at, "empty catch block"))
        for n, line in lines:
            if not line.strip():
                continue
            added_nonblank += 1
            comment = _is_comment(line, ext)
            if comment or n in doc_lines:
                comment_lines += 1
            if not comment:
                continue
            body = _comment_body(line)
            if _DIVIDER_RE.match(body):
                findings.append(_finding("fail", "divider", path, n, line.strip()))
            elif _FORENSIC_RE.search(body):
                findings.append(_finding("fail", "forensic-comment", path, n, line.strip()))
            elif _SHOUT_RE.search(body):
                findings.append(_finding("warn", "shouting", path, n, line.strip()))
    share = comment_lines / added_nonblank if added_nonblank else 0.0
    if added_nonblank >= LIMITS["min_added_for_share"]:
        if share > LIMITS["comment_share_fail"]:
            findings.append(_finding("fail", "comment-share", "", None, f"{share:.0%} of {added_nonblank} added lines are comments or docstrings"))
        elif share > LIMITS["comment_share_warn"]:
            findings.append(_finding("warn", "comment-share", "", None, f"{share:.0%} of {added_nonblank} added lines are comments or docstrings"))
    nfiles = sum(1 for p in files if not _SKIP.search(p))
    if added_total + removed > LIMITS["commit_lines"] or nfiles > LIMITS["commit_files"]:
        findings.append(_finding("warn", "large-commit", "", None, f"{added_total + removed} changed lines in {nfiles} files; split by behaviour"))
    return {
        "files": nfiles, "added": added_total, "removed": removed, "comment_lines": comment_lines,
        "comment_share": round(share, 3), "findings": findings,
        "ok": not any(f["level"] == "fail" for f in findings),
    }


_TRAILER_RE = re.compile(r"^[A-Za-z][A-Za-z-]+: \S")
_HEADING_RE = re.compile(r"^(?:#{1,6}\s|\*\*[^*]+\*\*:?\s*$|[A-Z][A-Z' ,/-]{3,}[.:]\s*$)")
_TRANSCRIPT_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:Ran|Tested|Verified|Passed|Verification)\b|^\s*(?:\$ |pytest\b|npm (?:test|run)\b)")


def analyze_message(text: str) -> Dict[str, Any]:
    lines = [l.rstrip() for l in text.splitlines() if not l.startswith("#")]
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and _TRAILER_RE.match(lines[-1]):
        lines.pop()
    content = [l for l in lines if l.strip()]
    subject = content[0] if content else ""
    body = content[1:]
    findings: List[Dict[str, Any]] = []
    if len(subject) > LIMITS["subject_chars"]:
        findings.append(_finding("warn", "long-subject", "", 1, f"{len(subject)} chars"))
    if len(body) > LIMITS["body_lines"]:
        findings.append(_finding("warn", "long-body", "", None, f"{len(body)} body lines, budget {LIMITS['body_lines']}"))
    for i, l in enumerate(body, 2):
        if _HEADING_RE.match(l.strip()):
            findings.append(_finding("fail", "headed-section", "", i, l.strip()))
        elif _TRANSCRIPT_RE.match(l):
            findings.append(_finding("warn", "transcript", "", i, l.strip()))
    return {"subject_chars": len(subject), "body_lines": len(body), "findings": findings,
            "ok": not any(f["level"] == "fail" for f in findings)}


def state_dir() -> Path:
    return Path(os.environ.get("DIFF_SHAPE_DIR") or (Path.home() / ".claude" / "diff_shape")).expanduser()


def get_mode() -> str:
    env = (os.environ.get("DIFF_SHAPE_MODE") or "").strip().lower()
    if env in MODES:
        return env
    cfg = state_dir() / "config.json"
    if not cfg.exists():
        return DEFAULT_MODE
    try:
        mode = str(json.loads(cfg.read_text("utf-8")).get("mode", "")).strip().lower()
    except (OSError, ValueError):
        return "off"
    return mode if mode in MODES else "off"


def set_mode(mode: str) -> Path:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    cfg = state_dir() / "config.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(json.dumps({"mode": mode, "set_at": _now()}, indent=2), "utf-8")
    return cfg


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append(row: Dict[str, Any]) -> None:
    p = state_dir() / "log.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _git(*args: str, cwd: Optional[str] = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", check=True).stdout


def _staged_blob(path: str) -> Optional[str]:
    try:
        return _git("show", f":{path}")
    except subprocess.CalledProcessError:
        return None


def _print(result: Dict[str, Any], kind: str, mode: str) -> None:
    fs = result["findings"]
    if not fs:
        return
    fails = sum(1 for f in fs if f["level"] == "fail")
    verdict = "commit refused" if (mode == "block" and fails) else "commit proceeds"
    sys.stderr.write(f"[diff-shape] {kind}: {len(fs)} finding(s), {fails} fail-class ({mode} mode; {verdict})\n")
    for f in fs:
        where = f"{f['path']}:{f['line']}" if f["path"] and f["line"] else (f["path"] or (f"line {f['line']}" if f["line"] else ""))
        sys.stderr.write(f"  {f['level']:<4} {f['code']:<20} {where:<28} {f['text']}\n")


def cmd_pre_commit() -> int:
    mode = get_mode()
    if mode == "off":
        return 0
    diff = _git("diff", "--cached", "--no-color", "--no-ext-diff", "-U0")
    result = analyze_diff(diff, _staged_blob)
    _print(result, "staged diff", mode)
    counts: Dict[str, int] = {}
    for f in result["findings"]:
        counts[f["code"]] = counts.get(f["code"], 0) + 1
    _append({"ts": _now(), "v": __version__, "kind": "diff", "mode": mode, "files": result["files"],
             "added": result["added"], "removed": result["removed"], "comment_share": result["comment_share"],
             "counts": counts, "ok": result["ok"]})
    return 1 if (mode == "block" and not result["ok"]) else 0


def cmd_commit_msg(path: str) -> int:
    mode = get_mode()
    if mode == "off":
        return 0
    result = analyze_message(Path(path).read_text("utf-8", errors="replace"))
    _print(result, "commit message", mode)
    _append({"ts": _now(), "v": __version__, "kind": "msg", "mode": mode, "subject_chars": result["subject_chars"],
             "body_lines": result["body_lines"], "ok": result["ok"]})
    return 1 if (mode == "block" and not result["ok"]) else 0


_SHIM = "#!/bin/sh\n# diff-shape (ConciseClaude): remove this file to uninstall.\n\"{py}\" \"{script}\" {cmd} \"$@\"\n"


def cmd_install(repo: Optional[str]) -> int:
    top = repo or _git("rev-parse", "--show-toplevel").strip()
    hooks = Path(_git("rev-parse", "--git-path", "hooks", cwd=top).strip())
    if not hooks.is_absolute():
        hooks = Path(top) / hooks
    hooks.mkdir(parents=True, exist_ok=True)
    py, script = Path(sys.executable).as_posix(), Path(__file__).resolve().as_posix()
    for name in ("pre-commit", "commit-msg"):
        target = hooks / name
        if target.exists() and "diff-shape" not in target.read_text("utf-8", errors="replace"):
            print(f"skip {target}: a hook already exists; call `{script} {name}` from it yourself")
            continue
        target.write_text(_SHIM.format(py=py, script=script, cmd=name), "utf-8")
        target.chmod(target.stat().st_mode | 0o111)
        print(f"wrote {target}")
    return 0


def cmd_report(days: float, as_json: bool) -> None:
    p = state_dir() / "log.jsonl"
    rows: List[Dict[str, Any]] = []
    if p.exists():
        cutoff = time.time() - days * 86400
        for line in p.read_text("utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
                if time.mktime(time.strptime(row["ts"], "%Y-%m-%dT%H:%M:%SZ")) - time.timezone >= cutoff:
                    rows.append(row)
            except (ValueError, KeyError):
                continue
    diffs = [r for r in rows if r.get("kind") == "diff"]
    msgs = [r for r in rows if r.get("kind") == "msg"]
    codes: Dict[str, int] = {}
    for r in diffs:
        for k, v in r.get("counts", {}).items():
            codes[k] = codes.get(k, 0) + v
    summary = {
        "days": days, "diffs": len(diffs), "messages": len(msgs),
        "median_comment_share": round(statistics.median(r["comment_share"] for r in diffs), 3) if diffs else None,
        "diffs_with_fail": sum(1 for r in diffs if not r.get("ok", True)),
        "median_body_lines": statistics.median(r["body_lines"] for r in msgs) if msgs else None,
        "findings_by_code": dict(sorted(codes.items(), key=lambda kv: -kv[1])),
    }
    print(json.dumps(summary, indent=2) if as_json else "\n".join(f"{k}: {v}" for k, v in summary.items()))


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Measure the shape of a staged diff and its commit message.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pre-commit")
    cm = sub.add_parser("commit-msg")
    cm.add_argument("path")
    ms = sub.add_parser("measure")
    ms.add_argument("--msg", action="store_true")
    ins = sub.add_parser("install")
    ins.add_argument("--repo")
    md = sub.add_parser("mode")
    md.add_argument("value", nargs="?", choices=MODES)
    rep = sub.add_parser("report")
    rep.add_argument("--days", type=float, default=7.0)
    rep.add_argument("--json", action="store_true")
    sub.add_parser("version")
    args = ap.parse_args(argv)

    if args.cmd in ("pre-commit", "commit-msg"):
        try:
            return cmd_pre_commit() if args.cmd == "pre-commit" else cmd_commit_msg(args.path)
        except Exception as exc:
            sys.stderr.write(f"[diff-shape] skipped: {exc}\n")
            return 0  # a broken meter must not cost a commit
    if args.cmd == "measure":
        text = sys.stdin.buffer.read().decode("utf-8", "replace")
        print(json.dumps(analyze_message(text) if args.msg else analyze_diff(text), indent=2))
    elif args.cmd == "install":
        return cmd_install(args.repo)
    elif args.cmd == "mode":
        print(f"mode={args.value} -> {set_mode(args.value)}" if args.value else get_mode())
    elif args.cmd == "report":
        cmd_report(args.days, args.json)
    elif args.cmd == "version":
        print(__version__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
