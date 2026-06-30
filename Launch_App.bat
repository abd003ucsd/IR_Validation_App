@echo off
setlocal enabledelayedexpansion

REM FIX (ISSUE 3): Enable ANSI Escape Code support for colored output
reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>nul
for /f %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "RED=%ESC%[31m"
set "RESET=%ESC%[0m"

REM FIX (ISSUE 2): If --skip-runas is passed, jump straight to env check.
REM This is how the runas-spawned session re-enters the script without prompting again.
if "%~1"=="--skip-runas" goto ENV_CHECK

REM FIX (ISSUE 5): Default to the -app variant of the current user's account.
REM The -app account holds valid Kerberos tickets that resolve the SQL Server
REM double-hop problem when pyodbc runs inside the Streamlit process.
set "APP_USER=%USERNAME%-app"
echo %YELLOW%[INFO]%RESET% Default -app account is %APP_USER%. %GREEN%Press Enter%RESET% to use it, or %YELLOW%type a different username%RESET%:
set "APP_INPUT="
set /p APP_INPUT="> "
if not "%APP_INPUT%"=="" set "APP_USER=%APP_INPUT%"

REM FIX (ISSUE 4): No cmdkey. Single clear instruction before runas.
echo %YELLOW%[INFO] When prompted, enter your -app password. You may see a Windows Credentials dialog — this is expected.%RESET%

REM FIX (ISSUE 1): Strip trailing backslash from %~dp0 before injecting into runas string.
REM %~dp0 always ends with \ which escapes the closing \" and breaks the runas command string.
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM FIX (ISSUE 1): Use pushd (not cd /d) for network/Q: drive compatibility.
REM FIX (ISSUE 5): Use cmd /k (not cmd /c) to keep terminal open so Streamlit
REM stdout and stderr remain visible to the user throughout the session.
REM FIX (ISSUE 5): runas /netonly means local UI stays as the regular user but all
REM network auth (SQL Server via pyodbc) uses the -app Kerberos credential.
runas /netonly /user:AD\%APP_USER% ^
    "cmd /k pushd \"%SCRIPT_DIR%\" && \"%SCRIPT_DIR%\Launch_App.bat\" --skip-runas"

REM Parent window exits after spawning the runas session. This is expected.
exit /b 0

:ENV_CHECK
REM FIX (ISSUE 1): Use pushd for reliable navigation on network/Q: drives.
pushd "%~dp0"

REM 1. Prefer bundled virtual environment
if exist "env\Scripts\python.exe" (
    "env\Scripts\python.exe" -c "import streamlit" >nul 2>nul
    if !ERRORLEVEL! equ 0 (
        set "PY_CMD=env\Scripts\python.exe"
        goto LAUNCH
    )
)

REM 2. Try system Python via py launcher
py -3 -c "import streamlit" >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "PY_CMD=py -3"
    goto LAUNCH
)

REM 3. Try system Python directly
python -c "import streamlit" >nul 2>nul
if !ERRORLEVEL! equ 0 (
    set "PY_CMD=python"
    goto LAUNCH
)

REM FIX (ISSUE 3): RED for [ERROR]
echo %RED%[ERROR]%RESET% Could not find a usable Python environment.
echo.
echo   - Virtual env (env\) was not found or is missing Streamlit
echo   - No system Python with Streamlit detected
echo.
echo Please run Setup_Environment.bat or contact the maintainer.
echo.
pause
popd
exit /b 1

:LAUNCH
REM FIX (ISSUE 3): YELLOW for [INFO]
echo %YELLOW%[INFO]%RESET% Launching IR Data Validation Tool...
%PY_CMD% -m streamlit run app.py
if !ERRORLEVEL! neq 0 (
    echo.
    REM FIX (ISSUE 3): RED for [ERROR]
    echo %RED%[ERROR]%RESET% Application failed to start.
    pause
)
popd
exit /b 0