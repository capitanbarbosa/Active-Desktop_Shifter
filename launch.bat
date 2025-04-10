@echo off
REM Check if venv exists, create if not
if not exist venv\ (
    python -m venv venv
    call venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
)

REM Launch both components
call venv\Scripts\activate
start venv\Scripts\pythonw.exe vSystemTray.py
start venv\Scripts\pythonw.exe Active-DesktopSwitcher.pyw 