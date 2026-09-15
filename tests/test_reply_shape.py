"""Tests for hooks/reply_shape.py. Run: python tests/test_reply_shape.py  (or pytest)."""
import importlib.util
import inspect
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "hooks" / "reply_shape.py"
_spec = importlib.util.spec_from_file_location("reply_shape", SCRIPT)
rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rs)

LONG = "word " * 120  # 599 prose chars


def run(cmd, payload, state, mode):
    env = {**os.environ, "REPLY_SHAPE_DIR": str(state), "REPLY_SHAPE_MODE": mode}
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), cmd],
        input=json.dumps(payload).encode("utf-8"),
        capture_output=True, env=env, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.decode("utf-8").strip()


def test_literals_do_not_count():
    text = "Short answer.\n```\n" + "x" * 2000 + "\n```\nSee `src/a/long/path.py:12` and https://example.com/" + "y" * 300
    shape = rs.measure(text)
    assert shape["prose_chars"] < 40 and shape["ok"]


def test_label_selects_protected_budget():
    assert rs.measure("**Risk:** " + LONG)["profile"] == "protected"
    plain = rs.measure(LONG)
    assert plain["profile"] == "default" and not plain["ok"]


def test_verdict_and_need_you_detected():
    shape = rs.measure("✅ **Done.**\nDetail.\n**Need you:** pick A or B")
    assert shape["verdict_first"] and shape["need_you_last"]


def test_block_mode_refuses_once(tmp_path):
    out = run("stop", {"session_id": "s1", "last_assistant_message": LONG}, tmp_path, "block")
    assert json.loads(out)["decision"] == "block"
    retry = {"session_id": "s1", "last_assistant_message": LONG, "stop_hook_active": True}
    assert run("stop", retry, tmp_path, "block") == ""
    assert len((tmp_path / "reply_shape.jsonl").read_text("utf-8").splitlines()) == 2


def test_nudge_fires_once_per_overage(tmp_path):
    run("stop", {"session_id": "s2", "last_assistant_message": LONG}, tmp_path, "nudge")
    first = run("prompt", {"session_id": "s2", "prompt": "next"}, tmp_path, "nudge")
    assert "over by" in json.loads(first)["hookSpecificOutput"]["additionalContext"]
    assert run("prompt", {"session_id": "s2", "prompt": "again"}, tmp_path, "nudge") == ""


def test_short_reply_is_silent(tmp_path):
    run("stop", {"session_id": "s3", "last_assistant_message": "✅ **ok**"}, tmp_path, "block")
    assert run("prompt", {"session_id": "s3", "prompt": "next"}, tmp_path, "nudge") == ""


def test_off_mode_still_logs_but_says_nothing(tmp_path):
    assert run("stop", {"session_id": "s4", "last_assistant_message": LONG}, tmp_path, "off") == ""
    assert run("prompt", {"session_id": "s4", "prompt": "next"}, tmp_path, "off") == ""
    assert (tmp_path / "reply_shape.jsonl").exists()


def test_verbose_stage_lasts_one_reply(tmp_path):
    run("prompt", {"session_id": "s5", "prompt": "/v explain the design"}, tmp_path, "block")
    assert run("stop", {"session_id": "s5", "last_assistant_message": LONG}, tmp_path, "block") == ""
    run("prompt", {"session_id": "s5", "prompt": "thanks"}, tmp_path, "off")
    assert run("stop", {"session_id": "s5", "last_assistant_message": LONG}, tmp_path, "block") != ""


def test_ultra_stage_tightens_budget(tmp_path):
    run("prompt", {"session_id": "s6", "prompt": "/u status?"}, tmp_path, "block")
    out = run("stop", {"session_id": "s6", "last_assistant_message": "word " * 40}, tmp_path, "block")
    assert json.loads(out)["decision"] == "block"


def test_transcript_fallback_reads_final_reply(tmp_path):
    events = [
        {"type": "user", "message": {"role": "user", "content": "hi"}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Interim."}, {"type": "tool_use", "name": "Bash"}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "Final answer."}]}},
    ]
    path = tmp_path / "t.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events), "utf-8")
    assert rs.final_reply_from_transcript(str(path)) == "Final answer."


def test_followup_signal_is_logged_and_reported(tmp_path):
    run("stop", {"session_id": "s7", "last_assistant_message": "✅ **ok**"}, tmp_path, "nudge")
    run("prompt", {"session_id": "s7", "prompt": "what do you mean by that?"}, tmp_path, "nudge")
    run("stop", {"session_id": "s7", "last_assistant_message": LONG}, tmp_path, "nudge")
    out = run("prompt", {"session_id": "s7", "prompt": "too long, tl;dr please"}, tmp_path, "nudge")
    assert "over by" in out  # followup rows must not hide the reply row from the nudge
    env = {**os.environ, "REPLY_SHAPE_DIR": str(tmp_path)}
    rep = subprocess.run([sys.executable, str(SCRIPT), "report", "--json"], capture_output=True, env=env, timeout=30)
    groups = json.loads(rep.stdout)["groups"]
    assert groups["all"]["n"] == 2
    assert groups["all"]["asked_more_pct"] == 50 and groups["all"]["asked_shorter_pct"] == 50


def test_plain_prompt_logs_no_signal(tmp_path):
    run("stop", {"session_id": "s8", "last_assistant_message": "✅ **ok**"}, tmp_path, "off")
    run("prompt", {"session_id": "s8", "prompt": "now fix the parser"}, tmp_path, "off")
    rows = [json.loads(x) for x in (tmp_path / "reply_shape.jsonl").read_text("utf-8").splitlines()]
    assert not any(r.get("kind") == "followup" for r in rows)


def test_protected_feedback_points_to_file_or_v():
    row = rs.measure("**Plan:** " + "word " * 250)
    assert row["profile"] == "protected" and not row["ok"]
    assert "/v" in rs.feedback(row, "nudge")


def test_bad_payload_never_fails(tmp_path):
    env = {**os.environ, "REPLY_SHAPE_DIR": str(tmp_path)}
    proc = subprocess.run([sys.executable, str(SCRIPT), "stop"], input=b"not json", capture_output=True, env=env, timeout=30)
    assert proc.returncode == 0 and proc.stdout == b""


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
