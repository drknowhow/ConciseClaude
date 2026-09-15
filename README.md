# ConciseClaude

A reply system for Claude Code: shorter, more direct answers with the same
depth of work behind them. It changes how much Claude **says**, not how much it
reads, thinks, or verifies. Optionally it adds [C3](https://github.com/drknowhow/code-context-control)
so Claude also *reads* less.

Version: see [`VERSION`](VERSION) · changes: [`CHANGELOG.md`](CHANGELOG.md) · license: Apache-2.0

## Install
1. `git clone https://github.com/drknowhow/ConciseClaude.git`
2. Open Claude Code in that folder and say: **"Read IMPLEMENT.md and implement it."**
3. Start a new session. Output styles and hooks load at session start.

**Upgrade:** `git pull`, then say the same thing. The install guide compares the
installed version (`reply_shape.py version`) with `VERSION` and walks the
changelog before replacing anything.

## What's in it
| Part | File | Job |
|---|---|---|
| Rules | `output-styles/concise.md` | The only copy of the rules: budget, reply grammar, cut list, never-cut list. Loads into the system prompt. |
| Pointer | `claude-md-snippet.md` | Three lines for `~/.claude/CLAUDE.md` so every surface finds the rules and nobody writes a second set. |
| Meter | `hooks/reply_shape.py` | Stop hook measures each final reply. Prompt hook tells Claude when the previous one ran long. |
| One-turn stages | `commands/v.md`, `commands/u.md` | `/v <ask>` lifts the budget for one reply. `/u <ask>` squeezes it to 150 chars. |
| Writing pass | `skills/human-prose/SKILL.md` | For prose other people read: PR descriptions, docs, tickets, email. |
| C3 (optional) | `c3/claude-md-snippet.md` | Installs C3 from PyPI (`code-context-control`) and tells Claude how to use it: map files, read single symbols, filter long output. Its own reply-style advisor is switched off. |
| Version | `VERSION`, `CHANGELOG.md` | One canonical version; `tests/test_version_sync.py` fails if any copy drifts. |
| Tests | `tests/` | `python tests/test_reply_shape.py` and `python tests/test_version_sync.py` (or pytest). |

## What a reply looks like
```
✅ Fixed: token expiry compared naive local time against UTC.
auth/middleware.py:42 now uses datetime.now(timezone.utc); 118 tests pass.
Need you: ship to staging now, or wait for the Monday window?
```
Result line first with a status glyph. Detail only if it changes your next
move. Literals verbatim. **Need you:** last, and only when Claude is blocked on
you. Security, destructive commands, errors, and plans get 900 chars, but only
under a visible label like **Risk:** or **Plan:**.

## Why it's built this way
Each point comes from running an earlier version of this system.
- **One copy of the rules.** The earlier setup had three overlapping rules: "≤4
  lines", "≤5 lines", and "400 chars". Replies drifted toward the loosest one.
- **Characters, not lines.** Lines wrap differently in a terminal, an IDE panel,
  and a phone. Prose characters outside code, tables, and URLs track what you
  actually read.
- **Exceptions are bounded and labeled.** An open-ended "never compress
  security, errors, planning, review" list covered most real work, so most
  replies qualified. Now the exception has a 900-char ceiling and needs a label,
  so taking it costs a visible word.
- **Measure at the output.** A rule nobody measures can't be tuned.
- **Never truncate.** Mechanical cutting would remove exactly the error text you
  needed.
- **Nudge before block.** Block mode makes Claude rewrite, but the rewrite lands
  *under* the long reply (rendered text can't be retracted), so you read both.
  Nudge only shapes the next reply.

## Evidence
About 2,200 measured replies over two weeks on the original setup:

| Phase | IDE median prose chars | IDE replies over budget | Chat-app replies over budget |
|---|---|---|---|
| Rules + grammar only | 648 | 62% | 40% |
| Rules + grammar + nudge | 532 | 55% | 21% |

Read this as a trend, not a controlled test: the two phases had different
session mixes. The nudge helped, but IDE replies still ran over budget more
often than not. Labels weren't being gamed (8% of replies), but 70% of labeled
replies went past 900 anyway. If nudge isn't enough, switch to block.

The original version measured length only. This one also records whether your
next prompt asked for **more** (`/v`, "what do you mean", "elaborate") or
**shorter** ("too long", "tl;dr", `/u`). That's the check on "concise without
losing quality": if `asked_more` climbs while the median falls, the budget is
cutting substance, so raise it. The original also silently skipped some replies
because it read the transcript before the final message was written. This
version reads the reply Claude Code hands the hook directly.

## Operating it
```
python ~/.claude/hooks/reply_shape.py report --days 7   # median, p90, % over, asked_more, asked_shorter
python ~/.claude/hooks/reply_shape.py mode block        # off | nudge (default) | block
```
- Budgets: the `BUDGETS` dict at the top of `reply_shape.py`.
- Rules: edit `~/.claude/output-styles/concise.md`, nowhere else.
- Privacy: the log stores sizes, flags, and a 12-character hash per reply. No
  reply text.
- Off switch: `mode off` stops all feedback but keeps measuring. Removing the
  two hook entries stops measuring too.
