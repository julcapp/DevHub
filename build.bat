@echo off
setlocal
cd /d "%~dp0"

echo [DevHub] Checking Python...
if exist ".venv\Scripts\python.exe" goto install

where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m venv .venv
  if errorlevel 1 goto failed
  goto install
)

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python 3.11 or newer is required.
  goto failed
)
python -m venv .venv
if errorlevel 1 goto failed

:install
echo [DevHub] Installing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo [DevHub] Environment ready. Starting application...
call "%~dp0start.bat"
exit /b %errorlevel%

:failed
echo.
echo [ERROR] DevHub setup failed. Copy the error message above.
pause
exit /b 1
