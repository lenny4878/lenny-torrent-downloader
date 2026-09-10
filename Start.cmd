@echo off
setlocal
cd /d "%~dp0"
if exist "dist\LennyTD.exe" (
  start "" "%~dp0dist\LennyTD.exe" %*
  exit /b 0
)
if not exist ".venv\Scripts\pythonw.exe" (
  echo Please run Setup.cmd first.
  pause
  exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0app.py" %*
