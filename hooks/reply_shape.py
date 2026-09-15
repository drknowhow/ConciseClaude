#!/usr/bin/env python3
"""Reply shape: measure the prose in each Claude Code reply and feed overage back.

Hooks (wire both in ~/.claude/settings.json):
  reply_shape.py stop     Stop hook. Measures the final reply and appends one JSONL
                          row. In block mode, refuses the stop once when over budget.
  reply_shape.py prompt   UserPromptSubmit hook. Records a /v or /u stage for the
                          coming reply, logs whether the prompt asks for more or
                          shorter (the quality signal), and in nudge/block mode
                          tells the model its previous reply was over budget.
Tools:
  reply_shape.py report [--days N] [--json]
  reply_shape.py mode [off|nudge|block]
  reply_shape.py measure [--profile P] < reply.txt
  reply_shape.py version

Stdlib only, Python 3.8+. A hook must never cost a turn: hook failures exit 0.
State: ~/.claude/reply_shape/ (override with REPLY_SHAPE_DIR). The log stores
sizes and a short hash per reply, never reply text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

__version__ = "1.1.0"  # must equal VERSION; tests/test_version_sync.py enforces it

# Prose characters allowed per reply, by profile. None = unbounded (still logged).
BUDGETS: Dict[str, Optional[int]] = {
    "default": 400,
    "protected": 900,
    "ultra": 150,
    "verbose": None,
}
MODES = ("off", "nudge", "block")
DEFAULT_MODE = "nudge"  # used when no config exists; block is always explicit
TAIL_BYTES = 1024 * 1024

# Literal regions are never prose. Order matters: fences before inline spans.
_FENCE_RE = re.compile(r"```.*?(?:```|\Z)|~~~.*?(?:~~~|\Z)", re.S)
_HTML_LITERAL_RE = re.compile(r"<pre\b.*?</pre>|<code\b.*?</code>", re.S | re.I)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_TABLE_LINE_RE = re.compile(r"^\s*\|.*\|\s*$", re.M)
_URL_RE = re.compile(r"https?://\S+")
_MARKUP_RE = re.compile(r"[*_~>#]+|<[^>\n]{1,40}>")
_HEADER_RE = re.compile(r"^\s{0,3}#{1,6}\s", re.M)

VERDICT_GLYPHS = ("✅", "⚠️", "⚠", "❌", "⏳")
NEED_YOU_RE = re.compile(r"\*\*Need you:\*\*", re.I)
RISK_RE = re.compile(r"\*\*Risk:\*\*", re.I)
PROTECTED_LABEL_RE = re.compile(
    r"^\s*(?:⚠️?\s*)?(?:\*\*)?"
    r"(?:Risk|Plan|Review|Error|Security|Migration|Destructive|Audit|Debug)"
    r":(?:\*\*)?",
    re.M | re.I,
)
_STAGE_RES = {
    "verbose": re.compile(r"^\s*/v(?:\s|$)|\[stage:verbose\]"),
    "ultra": re.compile(r"^\s*/u(?:\s|$)|\[stage:ultra\]"),
}
# Quality signal: what the user's next prompt says about the previous reply.
_FOLLOWUP_RES = {
    "more": re.compile(
        r"^\s*/v(?:\s|$)|\[stage:verbose\]|\b(?:more detail|more details|elaborate|explain (?:more|further|that|this|why)"
        r"|what do you mean|go deeper|expand on|say more|i don'?t (?:understand|follow)|not clear|unclear)\b",
        re.I,
    ),
    "shorter": re.compile(
        r"^\s*/u(?:\s|$)|\[stage:ultra\]|\b(?:shorter|too long|tl;?dr|too verbose|more concise|less verbose)\b",
        re.I,
    ),
}


# --- measurement -----------------------------------------------------------

def strip_literals(text: str) -> Tuple[str, int]:
    literal = 0

    def take(m: "re.Match[str]") -> str:
        nonlocal literal
        literal += len(m.group(0))
        return "\n"

    out = _FENCE_RE.sub(take, text)
    out = _HTML_LITERAL_RE.sub(take, out)
    out = _INLINE_CODE_RE.sub(take, out)
    out = _TABLE_LINE_RE.sub(take, out)
    out = _URL_RE.sub(take, out)
    return out, literal


def measure(text: str, profile: Optional[str] = None) -> Dict[str, Any]:
    """Measure one reply. Pure; never raises on string input."""
    text = text or ""
    prose_raw, literal = strip_literals(text)
    prose = " ".join(_MARKUP_RE.sub("", prose_raw).split())
    prof = (profile or ("protected" if PROTECTED_LABEL_RE.search(text) else "default")).lower()
    if prof not in BUDGETS:
        prof = "default"
    budget = BUDGETS[prof]
    over = max(0, len(prose) - budget) if budget is not None else 0
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    first = lines[0] if lines else ""
    last = lines[-1] if lines else ""
    return {
        "prose_chars": len(prose),
        "literal_chars": literal,
        "total_chars": len(text),
        "lines": len(lines),
        "has_table": bool(_TABLE_LINE_RE.search(text)),
        "has_header": bool(_HEADER_RE.search(text)),
        "verdict_first": first.startswith(VERDICT_GLYPHS),
        "need_you_last": bool(NEED_YOU_RE.search(last)),
        "has_risk": bool(RISK_RE.search(text)),
        "profile": prof,
        "budget": budget,
        "over_by": over,
        "ok": over == 0,
    }


def feedback(row: Dict[str, Any], kind: str) -> str:
    p, b, prof, o = row.get("prose_chars"), row.get("budget"), row.get("profile"), row.get("over_by")
    if kind == "nudge":
        lead = f"[reply-shape] Previous reply: {p} prose chars vs budget {b} ({prof}), over by {o}. Make this reply shorter."
    else:
        lead = f"reply-shape: {p} prose chars > {b} ({prof}), over by {o}. Rewrite the reply once, shorter. Don't mention this check."
    if prof == "protected":
        hint = (" Labeled replies still cap at 900: keep the decision, the risk and the literals in the reply; "
                "put background in a file, or offer /v.")
    else:
        hint = (" Cut narration; code, paths, commands and error text stay verbatim. Security, destructive, error, "
                "migration, planning and review replies get 900 only under a true **Risk:** / **Plan:** / "
                "**Error:** / **Review:** label.")
    if not row.get("verdict_first"):
        hint += " It also lacked a result line: start with a status glyph and a bold verdict."
    return lead + hint


# --- state -----------------------------------------------------------------

def state_dir() -> Path:
    return Path(os.environ.get("REPLY_SHAPE_DIR") or (Path.home() / ".claude" / "reply_shape")).expanduser()


def _safe(sid: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", sid)[:80] or "unknown"


def get_mode() -> str:
    env = (os.environ.get("REPLY_SHAPE_MODE") or "").strip().lower()
    if env in MODES:
        return env
    cfg = state_dir() / "config.json"
    if not cfg.exists():
        return DEFAULT_MODE
    try:
        mode = str(json.loads(cfg.read_text("utf-8")).get("mode", "")).strip().lower()
    except Exception:
        return "off"  # a broken switch fails toward silence, never toward blocking
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


def _log_path() -> Path:
    return state_dir() / "reply_shape.jsonl"


def _append(row: Dict[str, Any]) -> None:
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _tail_lines(path: Path) -> List[str]:
    try:
        with path.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            fh.seek(max(0, fh.tell() - TAIL_BYTES))
            return fh.read().decode("utf-8", "replace").splitlines()
    except (OSError, TypeError, ValueError):
        return []


def last_row(session_id: str) -> Optional[Dict[str, Any]]:
    for line in reversed(_tail_lines(_log_path())):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("session_id") == session_id and "prose_chars" in row:
            return row
    return None


def _stage_file(sid: str) -> Path:
    return state_dir() / "stage" / _safe(sid)


def _read_stage(sid: str) -> Optional[str]:
    try:
        value = _stage_file(sid).read_text("utf-8").strip()
    except OSError:
        return None
    return value if value in BUDGETS else None


def _clear_stage(sid: str) -> None:
    try:
        _stage_file(sid).unlink()
    except OSError:
        pass


def final_reply_from_transcript(path: str) -> str:
    """Text of the assistant messages after the last user/tool-result event."""
    parts: List[str] = []
    for line in reversed(_tail_lines(Path(path)) if path else []):
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if not isinstance(ev, dict):
            continue
        etype = ev.get("type")
        if etype == "user":
            break
        if etype != "assistant":
            continue
        content = (ev.get("message") or {}).get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            texts = [b.get("text") or "" for b in content if isinstance(b, dict) and b.get("type") == "text"]
            parts.append("\n".join(t for t in texts if t))
    return "\n\n".join(p for p in reversed(parts) if p.strip())


# --- hooks -----------------------------------------------------------------

def cmd_stop(payload: Dict[str, Any]) -> None:
    sid = str(payload.get("session_id") or "")
    text = payload.get("last_assistant_message")
    if not isinstance(text, str) or not text.strip():
        text = final_reply_from_transcript(str(payload.get("transcript_path") or ""))
    if not text.strip():
        return
    revision = bool(payload.get("stop_hook_active"))
    stage = _read_stage(sid) if sid else None
    shape = measure(text, profile=stage)
    _append({
        "ts": _now(),
        "session_id": sid,
        "sha": hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()[:12],
        "v": __version__,
        "revision": revision,
        **shape,
    })
    if not shape["ok"] and not revision and get_mode() == "block":
        # Claude Code sets stop_hook_active on the retry, so this can fire at most once per reply.
        print(json.dumps({"decision": "block", "reason": feedback(shape, "block")}))
        return
    if sid:
        _clear_stage(sid)


def cmd_prompt(payload: Dict[str, Any]) -> None:
    sid = str(payload.get("session_id") or "")
    if not sid:
        return
    prompt = str(payload.get("prompt") or "")
    stage = next((name for name, rx in _STAGE_RES.items() if rx.search(prompt)), None)
    if stage:
        path = _stage_file(sid)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(stage, "utf-8")
    else:
        _clear_stage(sid)

    row = last_row(sid)
    signal = next((name for name, rx in _FOLLOWUP_RES.items() if rx.search(prompt)), None)
    if row and signal:
        _append({"ts": _now(), "session_id": sid, "kind": "followup", "reply_sha": row.get("sha"),
                 "reply_profile": row.get("profile"), "signal": signal})

    if get_mode() == "off":
        return
    if not row or row.get("ok", True):
        return
    marker = state_dir() / "nudged" / _safe(sid)
    try:
        if marker.read_text("utf-8").strip() == row.get("sha"):
            return
    except OSError:
        pass
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(str(row.get("sha", "")), "utf-8")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": feedback(row, "nudge"),
        }
    }))


# --- tools -----------------------------------------------------------------

def _pct(part: int, whole: int) -> int:
    return round(100 * part / whole) if whole else 0


def _summary(rows: List[Dict[str, Any]], followups: Dict[str, set]) -> Dict[str, Any]:
    chars = sorted(int(r.get("prose_chars", 0)) for r in rows)
    n = len(rows)
    return {
        "n": n,
        "median": int(statistics.median(chars)) if chars else 0,
        "p90": chars[min(n - 1, int(0.9 * n))] if chars else 0,
        "over_pct": _pct(sum(1 for r in rows if not r.get("ok", True)), n),
        "verdict_first_pct": _pct(sum(1 for r in rows if r.get("verdict_first")), n),
        "asked_more_pct": _pct(sum(1 for r in rows if "more" in followups.get(r.get("sha", ""), ())), n),
        "asked_shorter_pct": _pct(sum(1 for r in rows if "shorter" in followups.get(r.get("sha", ""), ())), n),
    }


def cmd_report(days: float, as_json: bool) -> None:
    cutoff = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - days * 86400))
    rows: List[Dict[str, Any]] = []
    followups: Dict[str, set] = {}
    try:
        with _log_path().open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(row, dict) or str(row.get("ts", "")) < cutoff:
                    continue
                if row.get("kind") == "followup":
                    followups.setdefault(str(row.get("reply_sha")), set()).add(row.get("signal"))
                elif "prose_chars" in row and not row.get("revision"):
                    rows.append(row)
    except OSError:
        pass
    groups = {"all": rows}
    for prof in BUDGETS:
        subset = [r for r in rows if r.get("profile") == prof]
        if subset:
            groups[prof] = subset
    result = {
        "version": __version__, "days": days, "mode": get_mode(), "log": str(_log_path()),
        "last_reply_at": rows[-1]["ts"] if rows else None,
        "sessions": len({r.get("session_id") for r in rows}),
        "groups": {k: _summary(v, followups) for k, v in groups.items()},
    }
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"reply-shape {__version__} | last {days:g}d | mode={result['mode']} | {result['sessions']} sessions | "
          f"last reply logged {result['last_reply_at']}")
    print(f"{'profile':<10}{'n':>6}{'median':>8}{'p90':>7}{'over':>7}{'verdict1st':>12}{'asked_more':>12}{'asked_shorter':>15}")
    for name, s in result["groups"].items():
        print(f"{name:<10}{s['n']:>6}{s['median']:>8}{s['p90']:>7}{s['over_pct']:>6}%{s['verdict_first_pct']:>11}%"
              f"{s['asked_more_pct']:>11}%{s['asked_shorter_pct']:>14}%")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Measure Claude Code reply prose and feed overage back.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stop")
    sub.add_parser("prompt")
    rep = sub.add_parser("report")
    rep.add_argument("--days", type=float, default=7.0)
    rep.add_argument("--json", action="store_true")
    md = sub.add_parser("mode")
    md.add_argument("value", nargs="?", choices=MODES)
    ms = sub.add_parser("measure")
    ms.add_argument("--profile", choices=tuple(BUDGETS))
    sub.add_parser("version")
    args = ap.parse_args(argv)

    if args.cmd in ("stop", "prompt"):
        try:
            payload = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
            if isinstance(payload, dict):
                (cmd_stop if args.cmd == "stop" else cmd_prompt)(payload)
        except Exception as exc:  # a hook must never cost a turn
            if os.environ.get("REPLY_SHAPE_DEBUG"):
                sys.stderr.write(f"[reply_shape] {exc}\n")
        return 0
    if args.cmd == "report":
        cmd_report(args.days, args.json)
    elif args.cmd == "mode":
        if args.value:
            print(f"mode={args.value} -> {set_mode(args.value)}")
        else:
            print(get_mode())
    elif args.cmd == "version":
        print(__version__)
    elif args.cmd == "measure":
        print(json.dumps(measure(sys.stdin.buffer.read().decode("utf-8", "replace"), args.profile), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
