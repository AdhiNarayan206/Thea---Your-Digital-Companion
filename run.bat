@echo off
rem Launch Thea with no console window.
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" run.py
) else (
    start "" pythonw run.py
)
