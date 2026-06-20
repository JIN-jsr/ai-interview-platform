@echo off
setlocal
cd /d "%~dp0"

title AI Interview Platform
echo ============================================
echo AI Interview Platform
echo ============================================
echo.
echo Starting Streamlit app...
echo If the browser does not open automatically, copy the Local URL from this window.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found or broken: .venv
    echo Please run these commands in the project folder:
    echo.
    echo python -m venv .venv
    echo .venv\Scripts\activate
    echo pip install -r requirements.txt
    echo streamlit run app.py
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m streamlit run app.py %*

if errorlevel 1 (
    echo.
    echo Startup failed.
    echo Please check whether dependencies are installed:
    echo.
    echo .venv\Scripts\activate
    echo pip install -r requirements.txt
    echo streamlit run app.py
    echo.
    pause
    exit /b 1
)

echo.
echo App stopped.
pause
