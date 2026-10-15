#!/bin/sh
# Refreshes the diff meter copy that git shims call (see diff_shape.stable_script), when one exists.
root=${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}
stable="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/conciseclaude/diff_shape.py"
[ -f "$stable" ] && cp "$root/hooks/diff_shape.py" "$stable" 2>/dev/null
exit 0
