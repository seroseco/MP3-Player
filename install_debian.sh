#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "== Roy's PMP dependency setup (Debian) =="

if ! command -v apt-get >/dev/null 2>&1; then
  echo "Error: apt-get was not found. Run this script on Debian/Ubuntu."
  exit 1
fi

echo "[1/5] Installing system packages"
sudo apt-get update
sudo apt-get install -y \
  python3 \
  python3-venv \
  python3-pip \
  ffmpeg \
  mpv \
  libsdl2-2.0-0 \
  libsdl2-image-2.0-0 \
  libsdl2-mixer-2.0-0 \
  libsdl2-ttf-2.0-0

echo "[2/5] Creating virtual environment (.venv)"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

echo "[3/5] Activating virtual environment"
source .venv/bin/activate

echo "[4/5] Upgrading pip"
python -m pip install --upgrade pip setuptools wheel

echo "[5/5] Installing Python packages"
python -m pip install pygame mutagen pillow

echo ""
echo "Setup complete."
echo "Run example:"
echo "  source .venv/bin/activate"
echo "  python main.py"
