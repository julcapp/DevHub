@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [DevHub] Environment missing. Run build.bat first.
  pause
  exit /b 1
)
echo [DevHub] Starting application...
".venv\Scripts\python.exe" run.py
if errorlevel 1 (
  echo.
  echo [DevHub] Application exited with an error. Copy the error text above.
  pause
  exit /b 1
)
