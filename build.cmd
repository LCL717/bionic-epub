@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\build.py
) else (
  python scripts\build.py
)
exit /b %errorlevel%
