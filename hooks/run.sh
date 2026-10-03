#!/bin/sh
# Runs reply_shape.py under the first real Python >= 3.8: py -3, python3, python.
# The Windows Store stub fails the version probe, so it is skipped. No Python
# means no metering, never a blocked turn.
here=$(cd "$(dirname "$0")" && pwd)
for c in "py -3" python3 python; do
  ok=$($c -c 'import sys; print(sys.version_info >= (3, 8))' 2>/dev/null) || continue
  [ "$ok" = "True" ] && exec $c "$here/reply_shape.py" "$@"
done
[ -n "$REPLY_SHAPE_DEBUG" ] && echo "conciseclaude: no Python >= 3.8 found; reply meter off" >&2
exit 0
