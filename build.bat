@echo off
setlocal
cd /d "%~dp0"

echo [DevHub] Preparing MVP environment...
where py >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python launcher 'py' was not found. Install Python 3.11+ and retry.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo [DevHub] Running test suite...
python -m pytest
if errorlevel 1 (
  echo [ERROR] Tests failed. DevHub was not started.
  exit /b 1
)

echo [DevHub] MVP checks passed. Starting application...
python run.py
