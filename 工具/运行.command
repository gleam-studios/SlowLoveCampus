#!/bin/sh
set -eu
TOOL_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "$(uname -m)" in
  arm64|aarch64) PYTHON_BIN="$TOOL_DIR/Python/cpython-3.12.11-macos-aarch64-none/bin/python3.12" ;;
  x86_64) PYTHON_BIN="$TOOL_DIR/Python/cpython-3.12.11-macos-x86_64-none/bin/python3.12" ;;
  *) echo "Unsupported Mac architecture" >&2; exit 1 ;;
esac
if [ ! -x "$PYTHON_BIN" ]; then
  /bin/sh "$TOOL_DIR/bootstrap-python.sh"
fi
if [ "$#" -eq 0 ]; then
  "$PYTHON_BIN" -I -X utf8 "$TOOL_DIR/deploy.py" --run check
  printf '\nPress Return to close...'
  read -r _reply
else
  exec "$PYTHON_BIN" -I -X utf8 "$TOOL_DIR/deploy.py" --run "$@"
fi
