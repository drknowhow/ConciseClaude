"""Token, cost and latency A/B of the Concise style on vs off. Method: docs/token-ab-2026-10-03.md."""
import argparse
import concurrent.futures as cf
import json
import os
import random
import shutil
import statistics as st
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "reply_shape.py"
CODE_TOOLS = ["--permission-mode", "acceptEdits", "--tools", "Write,Edit,Bash,Read",
              "--allowedTools", "Bash(python *),Bash(pytest *),Bash(py *)",
              "--disallowedTools", f"Read({(Path.home() / '.claude').as_posix()}/**)"]
QA = [
    "What's the difference between a process and a thread? When should I use each in Python?",
    "My pytest suite passes locally but fails in GitHub Actions with ModuleNotFoundError: No module named 'src'. "
    "What's likely wrong and how do I fix it?",
    "Should I use Postgres or SQLite for a single-user desktop app that syncs to the cloud occasionally? Recommend one.",
    "Explain what a git rebase does versus a merge, and when rebase is dangerous.",
    "I want to add rate limiting to a FastAPI endpoint. Give me a plan.",
    "Review this function for bugs:\n```python\ndef avg(values):\n    total = 0\n    for v in values:\n"
    "        total += v\n    return total / len(values)\n```",
    "How do I safely delete all local git branches that have already been merged into main?",
    "Why might a React component re-render infinitely when I call setState inside useEffect?",
]
SLUGIFY = ("In the current directory, write slugify.py with a function slugify(text) that lowercases, transliterates "
           "accents to ASCII, replaces runs of non-alphanumerics with single hyphens, and strips leading/trailing "
           "hyphens. Add test_slugify.py with pytest tests, run them, and report.")
MULTI = {
    "ops": [
        "I'm getting intermittent 502s from nginx in front of a gunicorn Flask app under load. What could cause it?",
        "Workers are sync, 4 of them, and some requests take 20s calling an external API. Does that change your answer?",
        "Show me the gunicorn config change you'd make.",
        "What about the nginx side, any timeouts to adjust?",
        "How would I verify the fix under load?",
        "Summarize the final plan as a checklist.",
    ],
    "design": [
        "I'm designing a habit tracker backend: users, habits, daily check-ins, streaks. Propose a Postgres schema.",
        "Should streaks be stored or derived?",
        "Users travel across timezones. How does that affect check-ins and streaks?",
        "Write the SQL for the current-streak query given your schema.",
        "What indexes do I need?",
        "Any risks with this design at 1M users?",
    ],
    "code": [
        "Create a Python CLI todo.py that stores todos in todos.json with add, list and done commands, using argparse.",
        "Add a --priority flag (low/med/high) to add, and sort list output by priority.",
        "Write pytest tests in test_todo.py and run them.",
        "Add a clear-done command with a test, and run the tests.",
        "Move the JSON storage into storage.py and keep the tests passing.",
        "Summarize what the project contains now.",
    ],
}


def suite(name, reps):
    """Return (label, turns, uses_tools) conversations, each repeated `reps` times."""
    if name == "single":
        convs = [(f"qa{i}", [q], False) for i, q in enumerate(QA)] + [("slugify", [SLUGIFY], True)]
    else:
        convs = [(k, turns, k == "code") for k, turns in MULTI.items()]
    return [(label, turns, tools, rep) for label, turns, tools in convs for rep in range(reps)]


def write_settings(arm, workdir, plugin):
    if arm == "on" and plugin:
        settings = {}  # the plugin forces its style and brings its own hooks
    else:
        settings = {"outputStyle": "Concise" if arm == "on" else "default"}
    if arm == "on" and not plugin:
        def entry(sub):
            return [{"hooks": [{"type": "command", "command": f'"{sys.executable}" "{HOOK}" {sub}', "timeout": 10}]}]
        settings["hooks"] = {"Stop": entry("stop"), "UserPromptSubmit": entry("prompt")}
    path = workdir / "settings.json"
    path.write_text(json.dumps(settings), "utf-8")
    return path


def converse(claude, model, plugin, arm, label, turns, tools, rep):
    workdir = Path(tempfile.mkdtemp(prefix=f"ccab_{arm}_{label}_"))
    env = dict(os.environ, REPLY_SHAPE_DIR=str(workdir / ".reply_shape"))
    settings, sid, rows = write_settings(arm, workdir, plugin), str(uuid.uuid4()), []
    for turn, prompt in enumerate(turns):
        cmd = [claude, "-p", "--setting-sources", "project", "--settings", str(settings), "--strict-mcp-config",
               "--model", model, "--output-format", "json", "--session-id" if turn == 0 else "--resume", sid]
        cmd += CODE_TOOLS if tools else ["--tools", ""]
        if arm == "on" and plugin:
            cmd += ["--plugin-dir", plugin]
        start = time.monotonic()
        # The prompt goes on stdin: variadic flags like --tools would swallow a positional prompt.
        proc = subprocess.run(cmd, cwd=workdir, env=env, input=prompt, capture_output=True, text=True,
                              encoding="utf-8", timeout=900)
        wall = time.monotonic() - start
        base = {"arm": arm, "conv": label, "rep": rep, "turn": turn}
        try:
            result = json.loads(proc.stdout)
        except json.JSONDecodeError:
            rows.append({**base, "error": (proc.stdout + proc.stderr)[-300:]})
            break
        usage = result.get("usage", {})
        rows.append({**base, "out": usage.get("output_tokens", 0),
                     "in_new": usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0),
                     "in_cached": usage.get("cache_read_input_tokens", 0), "cost": result.get("total_cost_usd", 0),
                     "api_ms": result.get("duration_api_ms", 0), "wall_s": round(wall, 2),
                     "reply_chars": len(result.get("result") or "")})
    return rows


def run(args):
    claude = shutil.which("claude")
    if not claude:
        sys.exit("claude is not on PATH")
    jobs = [(arm, *conv) for conv in suite(args.suite, args.reps) for arm in ("off", "on")]
    random.Random(7).shuffle(jobs)
    with cf.ThreadPoolExecutor(args.parallel) as pool:
        rows = [r for res in pool.map(lambda j: converse(claude, args.model, args.plugin_dir, *j), jobs) for r in res]
    Path(args.out).write_text(json.dumps(rows, indent=1), "utf-8")
    print(f"{len(rows)} turns, {sum('error' in r for r in rows)} errors -> {args.out}")


def summary(args):
    rows = [r for r in json.loads(Path(args.rows).read_text("utf-8")) if "error" not in r]
    convs = sorted({r["conv"] for r in rows})
    print("conv     arm  turns  out_tok  in_new  in_cached  cost_usd  wall_s  reply_chars")
    for conv in convs + ["ALL"]:
        for arm in ("off", "on"):
            sel = [r for r in rows if r["arm"] == arm and conv in ("ALL", r["conv"])]
            total = {k: sum(r[k] for r in sel) for k in ("out", "in_new", "in_cached", "cost", "wall_s", "reply_chars")}
            print(f"{conv:8} {arm:4} {len(sel):5} {total['out']:8} {total['in_new']:7} {total['in_cached']:10} "
                  f"{total['cost']:9.2f} {total['wall_s']:7.0f} {total['reply_chars']:12}")
    print("\nper-session cost_usd, so between-run spread is visible:")
    for conv in convs:
        for arm in ("off", "on"):
            reps = sorted({r["rep"] for r in rows if r["conv"] == conv})
            per = [round(sum(r["cost"] for r in rows if (r["arm"], r["conv"], r["rep"]) == (arm, conv, rep)), 3)
                   for rep in reps]
            print(f"{conv:8} {arm:4} {per}  median {st.median(per):.3f}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run")
    p_run.add_argument("--suite", choices=("single", "multi"), required=True)
    p_run.add_argument("--model", default="sonnet")
    p_run.add_argument("--reps", type=int, default=3)
    p_run.add_argument("--parallel", type=int, default=6)
    p_run.add_argument("--out", default="rows.json")
    p_run.add_argument("--plugin-dir", help="run the on arm from this plugin directory instead of user-scope files")
    p_sum = sub.add_parser("summary")
    p_sum.add_argument("rows")
    args = parser.parse_args(argv)
    run(args) if args.cmd == "run" else summary(args)


if __name__ == "__main__":
    main()
