@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto prepare_games
py -3 -c "import sys; assert sys.version_info >= (3, 11)" >nul 2>&1
if errorlevel 1 goto use_python
py -3 -m venv .venv
if errorlevel 1 goto failed
goto prepare_games

:use_python
python -c "import sys; assert sys.version_info >= (3, 11)" >nul 2>&1
if errorlevel 1 (
  echo Install Python 3.11 or newer with PATH enabled, then run setup.bat again.
  pause
  exit /b 1
)
python -m venv .venv
if errorlevel 1 goto failed

:prepare_games
".venv\Scripts\python.exe" -c "import sys; assert sys.version_info >= (3, 11)"
if errorlevel 1 (
  echo Python 3.11 or newer is required. See PLAYING.md to recreate the environment.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" setup_arcade.py
if errorlevel 1 goto failed
echo Setup complete. Double-click start.bat to play.
exit /b 0

:failed
echo Setup did not finish. Check the message above and PLAYING.md, then run setup.bat again.
pause
exit /b 1
