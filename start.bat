@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Python virtual environment not found. Running setup...
  call setup.bat
  if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" arcade.py
if errorlevel 1 (
  echo Launcher failed. See the message above.
  pause
  exit /b 1
)
