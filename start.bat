@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Python virtual environment not found. Running setup...
  call setup.bat
  if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" setup_arcade.py --check >nul 2>&1
if errorlevel 1 (
  echo Some games or packages are missing. Preparing all six games...
  call setup.bat
  if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" arcade.py
if errorlevel 1 (
  echo Launcher failed. See the message above.
  pause
  exit /b 1
)
