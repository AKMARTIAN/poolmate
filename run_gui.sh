#!/usr/bin/env bash
#
# Portable launcher for the epMotion pooling GUI (macOS + Linux).
# Resolves its own folder, finds Python 3, checks Tkinter, then starts the GUI.
# Used by both the macOS .command file and the Linux .desktop launcher.

set -u

# --- resolve the directory this script lives in (follow symlinks) ----------
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [ "${SOURCE#/}" = "$SOURCE" ] && SOURCE="$DIR/$SOURCE"
done
DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null 2>&1 && pwd)"
cd "$DIR" || exit 1

# --- show an error both in the terminal and as a native dialog if possible -
fail() {
  echo "ERROR: $1" >&2
  if command -v osascript >/dev/null 2>&1; then
    osascript -e "display alert \"epMotion Pooling Helper\" message \"$1\"" >/dev/null 2>&1
  elif command -v zenity >/dev/null 2>&1; then
    zenity --error --title="epMotion Pooling Helper" --text="$1" >/dev/null 2>&1
  fi
  exit 1
}

# --- find a Python 3 interpreter -------------------------------------------
PY=""
for cand in python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then
    if "$cand" -c 'import sys; sys.exit(0 if sys.version_info[0] >= 3 else 1)' >/dev/null 2>&1; then
      PY="$cand"; break
    fi
  fi
done
[ -n "$PY" ] || fail "Python 3 was not found. Please install Python 3, then try again."

# --- make sure Tkinter (the GUI toolkit) is available ----------------------
if ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
  fail "Python 3 is installed but Tkinter is missing. Linux: install your distro's Tk package (e.g. 'sudo apt install python3-tk' or 'sudo dnf install python3-tkinter'). macOS: install Python from python.org (it includes Tkinter)."
fi

exec "$PY" pool_gui.py
