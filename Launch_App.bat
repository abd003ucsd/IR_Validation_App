@echo off
setlocal
cd /d %~dp0

:: 1. Prefer bundled portable environment
if exist "env\Scripts\python.exe" (
    set "PY_CMD=env\Scripts\python.exe"
    "env\Scripts\python.exe" -c "import streamlit" >nul 2>nul
    if %ERRORLEVEL% equ 0 goto LAUNCH
)

:: 2. Try system Python: py -3
py -3 -c "import streamlit" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=py -3"
    goto LAUNCH
)

:: 3. Try system Python: python
python -c "import streamlit" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=python"
    goto LAUNCH
)

:: 5. Error Message
echo [ERROR] Could not find a usable Python environment.
echo.
echo - portable env was not found
echo - Streamlit is not available
echo.
echo Please run Setup_Environment.bat or contact the maintainer.
echo.
pause
exit /b 1

:LAUNCH
echo [INFO] Launching IR Data Validation Tool...
%PY_CMD% -m streamlit run app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Application failed to start.
    pause
)
