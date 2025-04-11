@echo off
echo [INFO] Starting Active Desktop Shifter setup...
echo [DEBUG] Current directory: %CD%

REM Check virtual environment
if not exist venv\ (
    echo [INFO] Creating new virtual environment...
    python -m venv venv || (
        echo [ERROR] Failed to create virtual environment
        exit /b 1
    )
)

REM Install requirements
echo [INFO] Installing dependencies...
call venv\Scripts\activate || (
    echo [ERROR] Failed to activate virtual environment
    exit /b 1
)
python -m pip install --upgrade pip || (
    echo [ERROR] Failed to upgrade pip
    exit /b 1
)
pip install -r requirements.txt || (
    echo [ERROR] Failed to install requirements
    exit /b 1
)

REM Launch applications with visible windows
echo [INFO] Launching applications...
start "Virtual Desktop System Tray" /B venv\Scripts\pythonw.exe vSystemTray.py
start "Desktop Switcher UI" /B venv\Scripts\pythonw.exe Active-DesktopSwitcher.pyw

echo [SUCCESS] Launch sequence completed successfully
timeout /t 3 /nobreak >nul 