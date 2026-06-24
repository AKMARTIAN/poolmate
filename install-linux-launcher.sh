#!/usr/bin/env bash
#
# Run this ONCE on a Linux machine to create a double-clickable launcher.
# A .desktop file needs the absolute install path baked in, so it is generated
# here on the target machine rather than shipped pre-filled.
#
#   bash install-linux-launcher.sh
#
# Creates the launcher in the application menu and (if present) on the Desktop.

set -eu

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
chmod +x "$DIR/run_gui.sh" 2>/dev/null || true

write_desktop() {
  local target="$1"
  cat > "$target" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=epMotion Pooling Helper
Comment=Equimolar library pooling for the Eppendorf epMotion
Exec=$DIR/run_gui.sh
Path=$DIR
Terminal=false
Categories=Science;Biology;Education;Utility;
EOF
  chmod +x "$target"
}

APPS="$HOME/.local/share/applications"
mkdir -p "$APPS"
write_desktop "$APPS/epmotion-pooling.desktop"
echo "Installed to application menu: $APPS/epmotion-pooling.desktop"

if [ -d "$HOME/Desktop" ]; then
  write_desktop "$HOME/Desktop/epmotion-pooling.desktop"
  # Mark trusted so GNOME/Nautilus lets you double-click it.
  gio set "$HOME/Desktop/epmotion-pooling.desktop" metadata::trusted true 2>/dev/null || true
  echo "Placed launcher on the Desktop: $HOME/Desktop/epmotion-pooling.desktop"
fi

echo "Done. Look for 'epMotion Pooling Helper' in your apps, or double-click the Desktop icon."
