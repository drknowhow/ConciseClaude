#!/bin/sh
# Prints the rules pointer as session context, and refreshes the diff meter copy
# that git shims call (see diff_shape.stable_script) when one exists.
root=${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}
stable="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/conciseclaude/diff_shape.py"
[ -f "$stable" ] && cp "$root/hooks/diff_shape.py" "$stable" 2>/dev/null
cat <<EOF
## Replies (ConciseClaude)
- Reply rules live in \`$root/output-styles/concise.md\`, loaded as the Concise output style; code and commit rules in \`$root/rules/code.md\`, added on the first file edit. If the style isn't active (a subagent, another surface), read both files and follow them anyway. Subagent reports to a parent agent stay complete.
- Don't add reply-length or tone rules anywhere else. Two rule sets drift apart and the looser one wins.
- Before shipping prose other people read (PR descriptions, docs, tickets, emails), run the \`conciseclaude:human-prose\` skill.
EOF
exit 0
