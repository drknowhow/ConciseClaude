---
description: Install the diff meter's git pre-commit and commit-msg hooks in a repo
argument-hint: [repo path, default the current repo]
---
Install ConciseClaude's diff meter in the git repo at `$ARGUMENTS` (the current repo if empty).

1. Find Python 3.8 or newer: try `py -3`, then `python3`, then `python`, and skip any that fails `-c "import sys; assert sys.version_info >= (3, 8)"`.
2. Run `<python> "${CLAUDE_PLUGIN_ROOT}/hooks/diff_shape.py" install`, adding `--repo <path>` when a path was given.
3. If it prints `skip ...: a hook already exists`, show that line and ask before touching the existing hook.
4. Report which hook files were written. `diff_shape.py mode warn|block|off` and `report --days 7` work the same way.
