@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 (
    echo Setup failed. Install Python 3.11 or newer with PATH enabled.
    pause
    exit /b 1
  )
)
".venv\Scripts\python.exe" -c "import sys, tkinter; assert sys.version_info >= (3, 11), 'Python 3.11 or newer is required'"
if errorlevel 1 (
  echo Python 3.11+ and Tkinter are required for the sample game.
  pause
  exit /b 1
)
if exist "games\local\tesuto\requirements-web.txt" (
  ".venv\Scripts\python.exe" -m pip install -r "games\local\tesuto\requirements-web.txt"
  if errorlevel 1 (
    echo Failed to install the mole game's Excel reader. Check the message above.
    pause
    exit /b 1
  )
)
echo Setup complete. Double-click start.bat to play.
