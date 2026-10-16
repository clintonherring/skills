#!/usr/bin/env sh
# Thin wrapper: find a Python 3 and run install.py with the same arguments.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    exec "$py" "$DIR/install.py" "$@"
  fi
done
echo "Python 3.8 or newer is required."
echo "  macOS:  brew install python   (or https://www.python.org/downloads/)"
echo "  Linux:  sudo apt install python3   /   sudo dnf install python3"
exit 1
