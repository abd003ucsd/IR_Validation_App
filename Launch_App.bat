@echo off
setlocal
cd /d %~dp0

:: Break recursion — if already been through runas, skip to launch
if exist "%~dp0.app_launch_flag" (
    del "%~dp0.app_launch_flag"
    goto ENV_CHECK
)

:: Derive and confirm -app username
set "APP_USER=%USERNAME%-app"
echo [INFO] Database access requires your -app account.
set /p CONFIRM="Detected: AD\%APP_USER% — Press Enter to confirm or type a different username: "
if not "%CONFIRM%"=="" set "APP_USER=%CONFIRM%"

echo [INFO] Launching as AD\%APP_USER%...
echo You will be prompted for your -app password.
echo.

:: Create flag before runas so the new process skips Step 1
echo. > "%~dp0.app_launch_flag"

runas /netonly /user:AD\%APP_USER% ^
    "cmd /k cd /d %~dp0 && %~dp0Launch_App.bat"

if %ERRORLEVEL% neq 0 (
    del "%~dp0.app_launch_flag" >nul 2>nul
    echo.
    echo [ERROR] Launch failed. Common causes:
    echo   - Incorrect -app password
    echo   - AD\%APP_USER% does not exist
    echo.
    pause
)
exit /b

:ENV_CHECK
if exist "env\Scripts\python.exe" (
    set "PY_CMD=env\Scripts\python.exe"
    "env\Scripts\python.exe" -c "import streamlit" >nul 2>nul
    if %ERRORLEVEL% equ 0 goto LAUNCH
)

py -3 -c "import streamlit" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=py -3"
    goto LAUNCH
)

python -c "import streamlit" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=python"
    goto LAUNCH
)

echo [ERROR] Could not find a usable Python environment.
echo Please run Setup_Environment.bat or contact the maintainer.
pause
exit /b 1

:LAUNCH
echo [INFO] Launching IR Data Validation Tool...
%PY_CMD% -m streamlit run app.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Application failed to start.
    pause
)