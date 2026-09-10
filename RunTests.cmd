@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" tests\run_all.py
if errorlevel 1 (
  echo Tests failed. See the output above. Playback tests require requirements-dev.txt.
  pause
  exit /b 1
)
echo All tests passed. Report: docs\test-report.md
pause
