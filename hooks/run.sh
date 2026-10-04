#!/bin/sh
# Runs a hook script (first argument, relative to this directory) under the
# first real Python >= 3.8: py -3, python3, python. The Windows Store stub fails
# the version probe, so it is skipped. No Python means no hook, never a blocked turn.
here=$(cd "$(dirname "$0")" && pwd)
script=$1
shift
for c in "py -3" python3 python; do
  ok=$($c -c 'import sys; print(sys.version_info >= (3, 8))' 2>/dev/null) || continue
  [ "$ok" = "True" ] && exec $c "$here/$script" "$@"
done
[ -n "$REPLY_SHAPE_DEBUG" ] && echo "conciseclaude: no Python >= 3.8 found; $script skipped" >&2
exit 0
