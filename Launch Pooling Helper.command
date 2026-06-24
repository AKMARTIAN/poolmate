#!/usr/bin/env bash
# Double-click this on macOS to start the pooling GUI.
# (Finder opens it in Terminal; it just hands off to run_gui.sh.)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
exec "$DIR/run_gui.sh"
