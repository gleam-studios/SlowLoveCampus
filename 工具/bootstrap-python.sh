#!/bin/sh
# Native macOS bootstrap: no preinstalled Python is required.
set -eu
TOOL_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
[ "$(uname -s)" = Darwin ] || { echo "Only macOS is supported by this entry." >&2; exit 1; }
case "$(uname -m)" in
  arm64|aarch64) PLATFORM=macos-arm64 ;;
  x86_64) PLATFORM=macos-x64 ;;
  *) echo "Unsupported Mac architecture" >&2; exit 1 ;;
esac
MANIFEST="$TOOL_DIR/部署锁定.json"
URL=$(/usr/bin/plutil -extract "platforms.$PLATFORM.python.url" raw -o - "$MANIFEST")
EXPECTED=$(/usr/bin/plutil -extract "platforms.$PLATFORM.python.sha256" raw -o - "$MANIFEST")
DIRECTORY=$(/usr/bin/plutil -extract "platforms.$PLATFORM.python.directory" raw -o - "$MANIFEST")
EXECUTABLE=$(/usr/bin/plutil -extract "platforms.$PLATFORM.python.executable" raw -o - "$MANIFEST")
[ ! -x "$TOOL_DIR/$EXECUTABLE" ] || exit 0
[ ! -e "$TOOL_DIR/$DIRECTORY" ] || { echo "Incomplete existing Python directory; preserved. Check it before retrying." >&2; exit 1; }
mkdir -p "$TOOL_DIR/.cache/downloads" "$TOOL_DIR/Python"
LOCK="$TOOL_DIR/.cache/python-$PLATFORM.lock"
mkdir "$LOCK" 2>/dev/null || { echo "Python bootstrap is already running, or its lock needs checking." >&2; exit 1; }
STAGE=$(mktemp -d "$TOOL_DIR/Python/.install-XXXXXX")
trap 'rm -rf "$STAGE"; rmdir "$LOCK" 2>/dev/null || true' EXIT HUP INT TERM
ARCHIVE="$TOOL_DIR/.cache/downloads/$EXPECTED.tar.gz"
hash_ok() { [ -f "$1" ] && [ "$(/usr/bin/shasum -a 256 "$1" | cut -d ' ' -f 1)" = "$EXPECTED" ]; }
if ! hash_ok "$ARCHIVE"; then
  if ! hash_ok "$ARCHIVE.part"; then
    echo "Downloading pinned project Python for $PLATFORM..." >&2
    if /usr/bin/curl --fail --location --show-error --silent --retry 2 --connect-timeout 30 --continue-at - --output "$ARCHIVE.part" "$URL"; then
      :
    else
      RESULT=$?
      case "$RESULT" in
        22|33|36) /usr/bin/curl --fail --location --show-error --silent --retry 2 --connect-timeout 30 --output "$ARCHIVE.part" "$URL" ;;
        *) exit "$RESULT" ;;
      esac
    fi
  fi
  hash_ok "$ARCHIVE.part" || { rm -f "$ARCHIVE.part"; echo "Python archive SHA-256 mismatch; corrupt partial removed." >&2; exit 1; }
  mv "$ARCHIVE.part" "$ARCHIVE"
fi
/usr/bin/tar -xzf "$ARCHIVE" --strip-components=1 -C "$STAGE"
[ -x "$STAGE/bin/python3.12" ] || { echo "Python archive lacks the expected executable." >&2; exit 1; }
mv "$STAGE" "$TOOL_DIR/$DIRECTORY"
