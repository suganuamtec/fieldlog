@echo off
setlocal enabledelayedexpansion
title FieldLog Installer
color 0F

echo.
echo  ========================================
echo    FieldLog  ^|  UAM Deployment Entry
echo    Installer
echo  ========================================
echo.

:: ── Locate Python ──────────────────────────────────────────────────────────────
set PYTHON=
for %%P in (python python3) do (
    if not defined PYTHON (
        %%P --version >nul 2>&1 && set PYTHON=%%P
    )
)

if not defined PYTHON (
    echo  [ERROR] Python not found.
    echo.
    echo  Please install Python 3 from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%V in ('%PYTHON% --version 2^>^&1') do set PY_VER=%%V
echo  Found: %PY_VER%
echo.

:: ── Create / reuse virtualenv ─────────────────────────────────────────────────
set VENV=%~dp0.venv
if exist "%VENV%\Scripts\python.exe" (
    echo  [OK] Reusing existing virtualenv
) else (
    echo  Creating virtualenv...
    %PYTHON% -m venv "%VENV%"
    if errorlevel 1 (
        echo  [ERROR] Could not create virtualenv.
        pause
        exit /b 1
    )
    echo  [OK] Virtualenv created
)
set VENV_PY=%VENV%\Scripts\python.exe
echo.

:: ── Install dependencies into venv ────────────────────────────────────────────
echo  Installing dependencies...
"%VENV_PY%" -m pip install --quiet -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo.
    echo  [ERROR] pip install failed.
    echo.
    pause
    exit /b 1
)
echo  [OK] Dependencies installed
echo.

:: ── Create desktop shortcut ────────────────────────────────────────────────────
echo  Creating desktop shortcut...
"%VENV_PY%" "%~dp0install.py"
if errorlevel 1 (
    echo.
    echo  [WARN] Shortcut creation encountered an issue.
    echo         You can still launch with:  python launcher.py
)
echo.

:: ── Done ───────────────────────────────────────────────────────────────────────
echo  ========================================
echo    Installation complete!
echo    Launch FieldLog from your Desktop.
echo  ========================================
echo.
pause
