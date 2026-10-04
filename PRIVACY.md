# ConciseClaude privacy policy

ConciseClaude runs entirely on your computer. It has no server, makes no
network requests, sends no telemetry, and shares nothing with the author or
anyone else.

## What it reads
- The text of each finished Claude Code reply, in memory, to count its prose
  characters. The text is not saved.
- The session transcript file Claude Code already keeps, only to read which
  model the session uses (so it can skip Haiku) or to find the final reply.
- If you install the diff meter: your staged git diff and commit message, at
  commit time, to measure them. Neither is saved.

## What it stores, and where
All on your machine, under your home folder:
- `~/.claude/reply_shape/`: a log with, per reply, its size, the rule checks
  it passed, a 12-character hash and the session ID. No reply text. Also the
  meter mode and small per-session marker files.
- `~/.claude/diff_shape/` (diff meter only): counts per commit. No code.
- `~/.claude/conciseclaude/` (diff meter only): a copy of the meter script.

Nothing is retained anywhere else. Delete those folders at any time to
remove everything; uninstalling the plugin stops new writes.

## Personal data
ConciseClaude does not collect names, email addresses or any other personal
data, and it is not intended for children.

## Contact
Questions: https://github.com/drknowhow/ConciseClaude/issues
