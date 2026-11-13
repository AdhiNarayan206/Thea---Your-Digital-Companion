@echo off
setlocal
cd /d "%~dp0"

echo [Thea] Building Windows Desktop App...

if not exist ".venv\Scripts\pyinstaller.exe" (
    echo Error: PyInstaller not found in .venv.
    pause
    exit /b 1
)

.venv\Scripts\pyinstaller.exe --noconfirm Thea.spec

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo Build successful!
    echo Application located in: dist\Thea\Thea.exe
    echo ========================================================
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%.
)

pause

