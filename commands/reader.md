---
description: Tell Claude your technical level so explanations fit it (new, some, expert, or your own words)
argument-hint: new | some | expert | <your background in your own words> | clear
---
Set the reader level for ConciseClaude to: `$ARGUMENTS` (show the current one if empty).

1. Find Python 3.8 or newer: try `py -3`, then `python3`, then `python`, and skip any that fails `-c "import sys; assert sys.version_info >= (3, 8)"`.
2. Run `<python> "${CLAUDE_PLUGIN_ROOT}/hooks/reply_shape.py" reader <arguments>`, passing the arguments as one quoted string.
3. Show the output verbatim and write for that reader from this reply on.
