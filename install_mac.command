#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "== Roy's PMP dependency setup (macOS) =="

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: python3 was not found."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "[1/5] Creating virtual environment (.venv)"
  "$PYTHON_BIN" -m venv .venv
fi

echo "[2/5] Activating virtual environment"
source .venv/bin/activate

echo "[3/5] Upgrading pip"
python -m pip install --upgrade pip setuptools wheel

echo "[4/5] Installing Python packages"
python -m pip install pygame mutagen pillow

echo "[5/5] Checking/installing external tools (ffmpeg, ffplay, mpv)"
if command -v brew >/dev/null 2>&1; then
  if ! command -v ffmpeg >/dev/null 2>&1; then
    brew install ffmpeg
  else
    echo "- ffmpeg: already installed"
  fi

  if ! command -v ffplay >/dev/null 2>&1; then
    # ffplay is included in the ffmpeg package.
    brew install ffmpeg
  else
    echo "- ffplay: already installed"
  fi

  if ! command -v mpv >/dev/null 2>&1; then
    brew install mpv
  else
    echo "- mpv: already installed"
  fi
else
  echo "Homebrew is not available, skipping automatic ffmpeg/mpv installation."
  echo "Install manually if needed:"
  echo "  - https://brew.sh/"
  echo "  - brew install ffmpeg mpv"
fi

echo ""
echo "Setup complete."
echo "Run example:"
echo "  source .venv/bin/activate"
echo "  python main.py"
