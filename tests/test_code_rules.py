import inspect
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "hooks" / "code_rules.py"


def run(payload, state):
    env = {**os.environ, "REPLY_SHAPE_DIR": str(state)}
    proc = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps(payload).encode("utf-8"),
                          capture_output=True, env=env, timeout=30)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.decode("utf-8").strip()


def test_rules_sent_once_per_session(tmp_path):
    first = json.loads(run({"session_id": "a", "tool_name": "Write"}, tmp_path))
    assert first["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert "## Commits" in first["hookSpecificOutput"]["additionalContext"]
    assert run({"session_id": "a", "tool_name": "Edit"}, tmp_path) == ""
    assert run({"session_id": "b", "tool_name": "Edit"}, tmp_path) != ""


def test_haiku_session_gets_no_rules(tmp_path):
    transcript = tmp_path / "t.jsonl"
    transcript.write_text(json.dumps({"type": "assistant", "message": {"model": "claude-haiku-4-5", "content": []}}), "utf-8")
    assert run({"session_id": "h", "tool_name": "Write", "transcript_path": str(transcript)}, tmp_path) == ""


def test_bad_payload_is_silent(tmp_path):
    env = {**os.environ, "REPLY_SHAPE_DIR": str(tmp_path)}
    proc = subprocess.run([sys.executable, str(SCRIPT)], input=b"not json", capture_output=True, env=env, timeout=30)
    assert proc.returncode == 0 and proc.stdout == b""
    assert run({}, tmp_path) == ""


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted((n, f) for n, f in globals().items() if n.startswith("test_") and callable(f)):
        try:
            if "tmp_path" in inspect.signature(fn).parameters:
                with tempfile.TemporaryDirectory() as d:
                    fn(Path(d))
            else:
                fn()
            print(f"PASS {name}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {name}: {exc!r}")
    sys.exit(1 if failed else 0)
