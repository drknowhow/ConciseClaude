#!/bin/sh
# Prints the rules pointer as session context, and refreshes the diff meter copy
# that git shims call (see diff_shape.stable_script) when one exists.
root=${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}
stable="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/conciseclaude/diff_shape.py"
[ -f "$stable" ] && cp "$root/hooks/diff_shape.py" "$stable" 2>/dev/null
cat <<EOF
ConciseClaude (Sonnet and Opus; Haiku ignores this): reply rules in \`$root/output-styles/concise.md\`, code and repo-text rules in \`$root/rules/code.md\`. Where the style isn't active, such as in a subagent, read and follow both. Add no reply rules elsewhere. Run \`conciseclaude:human-prose\` before shipping prose others read.
EOF
exit 0
