@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo AI Interview Platform
echo ============================================
echo.
echo Starting Streamlit app...
echo If the browser does not open automatically, copy the Local URL from this window.
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment not found: .venv
    echo Please run:
    echo python -m venv .venv
    echo .venv\Scripts\activate
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
streamlit run app.py

if errorlevel 1 (
    echo.
    echo Startup failed.
    echo If you see "No Python at ...WindowsApps...", the virtual environment is broken.
    echo Recreate .venv and reinstall dependencies:
    echo.
    echo rmdir /s /q .venv
    echo python -m venv .venv
    echo .venv\Scripts\activate
    echo pip install -r requirements.txt
    echo streamlit run app.py
)

echo.
echo App stopped.
pause
