@echo off
setlocal
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Ready. Double-click Start.cmd.
pause
exit /b 0
:failed
echo Setup failed. Python 3.13 x64 and network access are required.
pause
exit /b 1
