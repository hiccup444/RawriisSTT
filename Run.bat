@echo off
:: RawriisSTT — source launcher for Windows
:: Double-click this to run the app. Missing packages are installed automatically.
python launcher.py
if errorlevel 1 (
    echo.
    echo Failed to start. Make sure Python 3.10+ is installed and on your PATH.
    pause
)
