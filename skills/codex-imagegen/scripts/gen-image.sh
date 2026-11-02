#!/bin/sh
# Backward-compatible POSIX entrypoint. Windows uses gen_image.py directly.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/gen_image.py" "$@"
elif command -v python >/dev/null 2>&1; then
  exec python "$SCRIPT_DIR/gen_image.py" "$@"
fi
echo 'codex-imagegen: Python 3.10+ is required.' >&2
exit 1
