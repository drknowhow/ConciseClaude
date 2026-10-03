---
description: Run the reply meter (report, mode) or the diff meter's report
argument-hint: report --days 7 | mode off|nudge|block | diff report --days 7
---
Run ConciseClaude's meter with these arguments: `$ARGUMENTS` (`report --days 7` if empty).

1. Find Python 3.8 or newer: try `py -3`, then `python3`, then `python`, and skip any that fails `-c "import sys; assert sys.version_info >= (3, 8)"`.
2. If the arguments start with `diff`, drop that word and run `<python> "${CLAUDE_PLUGIN_ROOT}/hooks/diff_shape.py" <rest>`. Otherwise run `<python> "${CLAUDE_PLUGIN_ROOT}/hooks/reply_shape.py" <arguments>`.
3. Show the output verbatim.
