@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" build.py
if errorlevel 1 (
  echo Build failed. Install requirements-build.txt first.
  pause
  exit /b 1
)
echo Built dist\LennyTD.exe
pause
