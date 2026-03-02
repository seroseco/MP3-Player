@echo off
setlocal ENABLEDELAYEDEXPANSION

cd /d "%~dp0"

echo == Roy's PMP dependency setup (Windows) ==

set "PYTHON_BIN="
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PYTHON_BIN=py -3"
) else (
  where python >nul 2>nul
  if %ERRORLEVEL%==0 (
    set "PYTHON_BIN=python"
  )
)

if "%PYTHON_BIN%"=="" (
  echo Error: Python was not found. Install Python 3 first.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/5] Creating virtual environment (.venv)
  %PYTHON_BIN% -m venv .venv
)

echo [2/5] Activating virtual environment
call ".venv\Scripts\activate.bat"

echo [3/5] Upgrading pip
python -m pip install --upgrade pip setuptools wheel

echo [4/5] Installing Python packages
python -m pip install pygame mutagen pillow

echo [5/5] Checking/installing external tools (ffmpeg, ffplay, mpv)
where winget >nul 2>nul
if %ERRORLEVEL%==0 (
  where ffmpeg >nul 2>nul
  if not %ERRORLEVEL%==0 (
    winget install -e --id Gyan.FFmpeg
  ) else (
    echo - ffmpeg: already installed
  )

  where ffplay >nul 2>nul
  if not %ERRORLEVEL%==0 (
    winget install -e --id Gyan.FFmpeg
  ) else (
    echo - ffplay: already installed
  )

  where mpv >nul 2>nul
  if not %ERRORLEVEL%==0 (
    winget install -e --id MPV.net
  ) else (
    echo - mpv: already installed
  )
) else (
  echo winget is not available, skipping automatic ffmpeg/mpv installation.
  echo Install manually if needed:
  echo   - FFmpeg: https://ffmpeg.org/download.html
  echo   - MPV: https://mpv.io/installation/
)

echo.
echo Setup complete.
echo Run example:
echo   call .venv\Scripts\activate.bat
echo   python main.py

endlocal

