#!/usr/bin/env python3
"""PostToolUse hook: on a session's first file edit, add rules/code.md to the context.

Reads the hook payload on stdin. Prints the rules once per session id; later
calls print nothing. Never fails the tool call.
"""
import json
import os
import re
import sys
from pathlib import Path

RULES = Path(__file__).resolve().parent.parent / "rules" / "code.md"


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    sid = re.sub(r"[^A-Za-z0-9_-]", "_", str(payload.get("session_id") or ""))[:80]
    if not sid or not RULES.exists():
        return 0
    state = Path(os.environ.get("REPLY_SHAPE_DIR") or (Path.home() / ".claude" / "reply_shape")).expanduser()
    marker = state / "code_rules" / sid
    if marker.exists():
        return 0
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("sent", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                             "additionalContext": RULES.read_text("utf-8")}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
