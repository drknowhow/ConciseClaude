#!/usr/bin/env python3
"""Reply shape: measure the prose in each Claude Code reply and feed overage back.

  reply_shape.py stop     Stop hook: measures the final reply, logs one row; block mode refuses once.
  reply_shape.py prompt   UserPromptSubmit hook: records /v or /u, logs the quality signal, nudges.
  reply_shape.py report [--days N] [--json] | mode [off|nudge|block] | measure [--profile P] | version

Stdlib only, Python 3.8+. Hook failures exit 0, so a hook never costs a turn.
State: ~/.claude/reply_shape/ (REPLY_SHAPE_DIR); the log stores sizes, tell counts and a hash per reply, never text.
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

__version__ = "6.3.1"  # must equal VERSION; tests/test_version_sync.py enforces it

# Prose characters allowed per reply, by profile. None = unbounded (still logged).
BUDGETS: Dict[str, Optional[int]] = {
    "default": 600,
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
_TABLE_RULE_RE = re.compile(r"^\s*\|[\s:|-]*-[\s:|-]*\|\s*$", re.M)  # |---|:--:|
_URL_RE = re.compile(r"https?://\S+")
# Markup is not read. A <...> span is a tag only if it names an HTML element and
# carries nothing but name=value (or known boolean) attributes, so prose such as
# "if a <b and c> d" or "Dict<str, int>" still counts.
_TAG_NAMES = (
    "a|abbr|b|blockquote|br|code|dd|del|details|div|dl|dt|em|h[1-6]|hr|i|img|ins|kbd|li|mark|"
    "ol|p|pre|q|s|samp|small|span|strike|strong|sub|summary|sup|table|tbody|td|tfoot|th|thead|"
    "tr|tt|u|ul|var"
)
_TAG_RE = re.compile(
    r"</?(?:" + _TAG_NAMES + r")"
    r"(?:\s+(?:[\w:-]+\s*=\s*(?:\"[^\"\n]*\"|'[^'\n]*'|[^\s\"'<>]+)|open|hidden))*"
    r"\s*/?>",
    re.I,
)
_MARKUP_RE = re.compile(r"[*_~]+|^[ \t]*(?:>[ \t]*)+|^[ \t]{0,3}#{1,6}(?=\s)", re.M)
_HEADER_RE = re.compile(r"^\s{0,3}#{1,6}\s", re.M)

# The 6.0 tags, plus the older glyph line that other rule sets still ask for.
VERDICT_RE = re.compile(r"^(?:\*\*(?:DONE|CAVEAT|BLOCKED|WORKING)\*\*|[✅⚠❌⏳])")
NEED_YOU_RE = re.compile(r"\*\*Need you:\*\*", re.I)
RISK_RE = re.compile(r"\*\*Risk:\*\*", re.I)
# A label is bold: "**Plan:**", "**Risk: headline.**", "⚠️ **Risk:**", on any line.
# An unformatted "Plan:" or a quoted "ERROR:" log line is not a label.
PROTECTED_LABEL_RE = re.compile(
    r"^\s*(?:⚠️?\s*)?\*\*"
    r"(?:Risk|Plan|Review|Error|Security|Migration|Destructive|Audit|Debug)"
    r":",
    re.M | re.I,
)
_STAGE_RES = {
    "verbose": re.compile(r"^\s*/(?:conciseclaude:)?v(?:\s|$)|\[stage:verbose\]"),
    "ultra": re.compile(r"^\s*/(?:conciseclaude:)?u(?:\s|$)|\[stage:ultra\]"),
}
# Only the explicit stages count: "explain this" or "shorter" refer to the code
# at least as often as to the reply.
_FOLLOWUP_SIGNALS = {"verbose": "more", "ultra": "shorter"}
# Writing tells, counted on prose with code and URLs removed. Logged and reported, never nudged on.
TELLS: Dict[str, "re.Pattern[str]"] = {
    "metaphor": re.compile(
        r"\bload[- ]bearing\b|\bseams?\b|\bearns? (?:its|their) (?:keep|place)\b|"
        r"\bdoing (?:a lot of|real|the heavy) (?:work|lifting)\b|\bsmoking gun\b|\bthe unlock\b", re.I),
    "contrast": re.compile(
        r"\b(?:it|this|that)(?:'s| is| was)(?:n't| not) (?:just |only |merely |simply |about )?[^.;\n]{1,60}"
        r"[.;,—]\s*(?:it|this|that|they)(?:'s| is| was| are)\b|\brather than (?:merely|simply|just)\b|"
        r"\bnot (?:just|only|merely) [^.;\n]{1,40}, but\b", re.I),
    "salience": re.compile(
        r"\b(?:this|that|which) (?:really )?matters\b|\bworth (?:noting|naming|flagging|calling out|stating)\b|"
        r"\bthe real (?:problem|issue|story|question|win|answer|work)\b|"
        r"\bhere'?s the (?:thing|kicker|catch|twist|part)\b|\bthat'?s the (?:tell|whole (?:thing|point))\b", re.I),
    "sincerity": re.compile(r"\b(?:honestly|genuinely|truly|frankly)\b|\bthe honest (?:answer|take|version)\b", re.I),
    "overclaim": re.compile(
        r"\bproduction[- ]ready\b|\bfully (?:verified|tested|working|functional)\b|\b100% (?:verified|working)\b|"
        r"\bno regressions\b", re.I),
    "sycophancy": re.compile(
        r"\byou'?re (?:absolutely|completely|totally) (?:right|correct)\b|\b(?:great|excellent) (?:question|catch)\b", re.I),
    "offer": re.compile(r"\b(?:want me to|shall i|would you like me to|say the word)\b", re.I),
    "arrow": re.compile(r"→|⇒|(?<=\s)->(?=\s)"),
    "emoji": re.compile(r"[\u2600-\u27bf\u23f3\u25b8\u2b50\U0001f300-\U0001faff]"),
    "em_dash": re.compile("—"),
    "bold": re.compile(r"\*\*[^*\n]+\*\*"),
}
# The status tags and labels the rules ask for are removed before counting tells.
_SANCTIONED_BOLD_RE = re.compile(
    r"\*\*(?:DONE|CAVEAT|BLOCKED|WORKING|(?:Risk|Plan|Review|Error|Security|Migration|Destructive|Audit|Debug|"
    r"Need you):[^*\n]*)\*\*",
    re.I,
)

# A plain ask for depth lifts the budget for that reply but is not a follow-up
# signal, so it never counts as "asked for more" in the report.
_DEPTH_RE = re.compile(
    r"\b(?:in[- ]depth|in (?:full|great|more) detail|in detail|full picture|deep dive|comprehensive(?:ly)?|"
    r"thorough(?:ly)?|as much (?:space|detail|room) as)\b",
    re.I,
)


def strip_literals(text: str) -> Tuple[str, int]:
    literal = 0

    def take(m: "re.Match[str]", repl: str = "\n") -> str:
        nonlocal literal
        literal += len(m.group(0))
        return repl

    def cells(m: "re.Match[str]") -> str:
        # Pipes are scaffolding; the cell text is prose and stays in.
        nonlocal literal
        literal += m.group(0).count("|")
        return m.group(0).replace("|", " ")

    out = _FENCE_RE.sub(take, text)
    out = _HTML_LITERAL_RE.sub(take, out)
    out = _INLINE_CODE_RE.sub(lambda m: take(m, " "), out)  # a space keeps table rows whole
    out = _TABLE_RULE_RE.sub(take, out)
    out = _TABLE_LINE_RE.sub(cells, out)
    out = _URL_RE.sub(take, out)
    return out, literal


def measure(text: str, profile: Optional[str] = None) -> Dict[str, Any]:
    """Measure one reply. Pure; never raises on string input."""
    text = text or ""
    prose_raw, literal = strip_literals(text)
    prose = " ".join(_MARKUP_RE.sub("", _TAG_RE.sub("", prose_raw)).split())
    scan = _SANCTIONED_BOLD_RE.sub(" ", prose_raw)
    tells = {name: n for name, rx in TELLS.items() if (n := len(rx.findall(scan)))}
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
        "verdict_first": bool(VERDICT_RE.match(first)),
        "need_you_last": bool(NEED_YOU_RE.search(last)),
        "has_risk": bool(RISK_RE.search(text)),
        "tells": tells,
        "profile": prof,
        "budget": budget,
        "over_by": over,
        "ok": over == 0,
    }


def feedback(row: Dict[str, Any], kind: str) -> str:
    p, b, prof, o = row.get("prose_chars"), row.get("budget"), row.get("profile"), row.get("over_by")
    if kind == "nudge":
        lead = (f"[reply-shape] Previous reply: {p} prose chars vs budget {b} ({prof}), over by {o}. "
                "Make this reply shorter by cutting points; keep each sentence whole.")
    else:
        lead = f"reply-shape: {p} prose chars > {b} ({prof}), over by {o}. Rewrite the reply once, shorter. Don't mention this check."
    if prof == "protected":
        hint = (" Labeled replies still cap at 900: keep the decision, the risk and the literals in the reply; "
                "put background in a file, or offer /v.")
    else:
        hint = (" Cut narration, not articles or verbs; code, paths, commands and error text stay verbatim. "
                "Security, destructive, error, "
                "migration, planning and review replies get 900 only under a true **Risk:** / **Plan:** / "
                "**Error:** / **Review:** label.")
    if not row.get("verdict_first"):
        hint += " It also lacked a result line: start with a bold status tag such as **DONE**, then the verdict."
    return lead + hint


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
    except (OSError, ValueError, AttributeError):
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
    _stage_file(sid).unlink(missing_ok=True)


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
    signal = _FOLLOWUP_SIGNALS.get(stage or "")
    if not stage and _DEPTH_RE.search(prompt):
        stage = "verbose"
    if stage:
        path = _stage_file(sid)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(stage, "utf-8")
    else:
        _clear_stage(sid)

    row = last_row(sid)
    if row and signal:
        _append({"ts": _now(), "session_id": sid, "kind": "followup", "reply_sha": row.get("sha"),
                 "reply_profile": row.get("profile"), "signal": signal})

    if get_mode() == "off":
        return
    if not row or row.get("ok", True):
        return
    marker = state_dir() / "nudged" / _safe(sid)
    if marker.exists() and marker.read_text("utf-8").strip() == row.get("sha"):
        return
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(str(row.get("sha", "")), "utf-8")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": feedback(row, "nudge"),
        }
    }))


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


def _tell_rates(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Per category: occurrences per 100 replies and the share of replies with any. Older rows have no tells."""
    scored = [r.get("tells") for r in rows if isinstance(r.get("tells"), dict)]
    rates = {}
    for name in TELLS:
        counts = [int(t.get(name, 0)) for t in scored]
        if any(counts):
            rates[name] = {"per_100": round(100 * sum(counts) / len(counts), 1),
                           "pct": _pct(sum(1 for c in counts if c), len(counts))}
    return rates


def cmd_report(days: float, as_json: bool) -> None:
    cutoff = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - days * 86400))
    rows: List[Dict[str, Any]] = []
    followups: Dict[str, set] = {}
    lines = _log_path().read_text("utf-8", errors="replace").splitlines() if _log_path().exists() else []
    for line in lines:
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
        "label_pct": _pct(len(groups.get("protected", [])), len(rows)),
        "tells": _tell_rates(rows),
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
    print(f"labeled (protected budget): {result['label_pct']}% of replies. Much above 20% means labels are buying room.")
    if result["tells"]:
        print("writing tells (logged only): " + ", ".join(
            f"{name} {t['per_100']}/100 replies in {t['pct']}%" for name, t in result["tells"].items()))


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
