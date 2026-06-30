@echo off
setlocal enabledelayedexpansion

REM FIX (ISSUE 1): pushd for network/Q: drive compatibility
pushd "%~dp0"

REM FIX (ISSUE 3): Enable ANSI color support
reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>nul
for /f %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "RED=%ESC%[31m"
set "RESET=%ESC%[0m"

REM ==========================================
REM STEP 1 — Check if Python 3.10+ is available
REM ==========================================
echo %YELLOW%[INFO]%RESET% Checking if Python is already available...
py -3 --version >nul 2>nul
if !ERRORLEVEL! equ 0 goto STEP3
python --version >nul 2>nul
if !ERRORLEVEL! equ 0 goto STEP3

REM Neither worked — check known user install path first before downloading
REM Python 3.10 user-only installs land here by default
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    echo %YELLOW%[INFO]%RESET% Python found at known install path. Adding to session PATH...
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python310;%LOCALAPPDATA%\Programs\Python\Python310\Scripts;%PATH%"
    goto STEP3
)

REM ==========================================
REM STEP 2 — Download and install Python 3.10.9
REM ==========================================
:STEP2
echo %YELLOW%[INFO]%RESET% Python not found. Downloading Python 3.10.9 installer...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.9/python-3.10.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"
if !ERRORLEVEL! neq 0 (
    echo %RED%[ERROR]%RESET% Failed to download Python 3.10.9.
    pause
    popd
    exit /b 1
)

echo %YELLOW%[INFO]%RESET% Installing Python 3.10.9 silently...
"%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
if !ERRORLEVEL! neq 0 (
    echo %RED%[ERROR]%RESET% Python 3.10.9 installation failed.
    pause
    popd
    exit /b 1
)

REM Wait for installer to finish registering
timeout /t 5 /nobreak >nul

REM FIX: PrependPath=1 updates the registry but NOT the current CMD session PATH.
REM Manually inject the known user install path into the current session so
REM subsequent py/python calls work without opening a new terminal.
set "PATH=%LOCALAPPDATA%\Programs\Python\Python310;%LOCALAPPDATA%\Programs\Python\Python310\Scripts;%PATH%"

REM Also pull the updated user PATH from registry to catch any non-default install locations
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do (
    set "PATH=%%b;%PATH%"
)

REM Re-check after PATH refresh
python --version >nul 2>nul
if !ERRORLEVEL! neq 0 (
    echo %RED%[ERROR]%RESET% Python still not accessible after install. Please restart and re-run setup.
    pause
    popd
    exit /b 1
)
echo %GREEN%[SUCCESS]%RESET% Python 3.10.9 installed and accessible.

REM ==========================================
REM STEP 3 — Check ODBC Driver (17 or 18)
REM ==========================================
:STEP3
echo %YELLOW%[INFO]%RESET% Checking for ODBC Driver 17 or 18 for SQL Server...
reg query "HKLM\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 18 for SQL Server" >nul 2>nul
if !ERRORLEVEL! equ 0 (
    echo %YELLOW%[INFO]%RESET% ODBC Driver 18 already present.
    goto STEP4
)
reg query "HKLM\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 17 for SQL Server" >nul 2>nul
if !ERRORLEVEL! equ 0 (
    echo %YELLOW%[INFO]%RESET% ODBC Driver 17 already present.
    goto STEP4
)

REM Neither driver found — check for bundled MSI
set "HAS_MSI=0"
if exist "%~dp0driver\" (
    for %%f in ("%~dp0driver\*.msi") do set "HAS_MSI=1"
)

if "!HAS_MSI!"=="1" (
    echo %YELLOW%[INFO]%RESET% Installing ODBC Driver from driver\ folder...
    for %%f in ("%~dp0driver\*.msi") do (
        echo %YELLOW%[INFO]%RESET% Installing %%~nxf...
        start /wait "" msiexec /i "%%f" /quiet /norestart
    )
    reg query "HKLM\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 18 for SQL Server" >nul 2>nul
    if !ERRORLEVEL! neq 0 (
        reg query "HKLM\SOFTWARE\ODBC\ODBCINST.INI\ODBC Driver 17 for SQL Server" >nul 2>nul
        if !ERRORLEVEL! neq 0 (
            echo %RED%[ERROR]%RESET% ODBC Driver installation failed.
            pause
            popd
            exit /b 1
        )
    )
    echo %GREEN%[SUCCESS]%RESET% ODBC Driver installed.
) else (
    REM No MSI bundled — give user a clear instructional message
    echo %YELLOW%[INFO]%RESET% ODBC Driver not found and no installer was bundled.
    echo.
    echo   Please download Microsoft ODBC Driver 18 for SQL Server from:
    echo   https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
    echo.
    echo   Then re-run this setup script.
    pause
    popd
    exit /b 1
)

REM ==========================================
REM STEP 4 — Virtual environment + dependencies
REM ==========================================
:STEP4
if not exist "env\Scripts\python.exe" (
    echo %YELLOW%[INFO]%RESET% Creating virtual environment...
    py -3 -m venv env >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        python -m venv env >nul 2>&1
        if !ERRORLEVEL! neq 0 (
            echo %RED%[ERROR]%RESET% Failed to create virtual environment.
            pause
            popd
            exit /b 1
        )
    )
)

echo %YELLOW%[INFO]%RESET% Activating virtual environment...
call env\Scripts\activate.bat
if !ERRORLEVEL! neq 0 (
    echo %RED%[ERROR]%RESET% Failed to activate virtual environment.
    pause
    popd
    exit /b 1
)

echo %YELLOW%[INFO]%RESET% Upgrading pip...
python -m pip install --upgrade pip
if !ERRORLEVEL! neq 0 (
    echo %RED%[ERROR]%RESET% Failed to upgrade pip.
    pause
    popd
    exit /b 1
)

echo %YELLOW%[INFO]%RESET% Installing requirements...
pip install -r requirements.txt
if !ERRORLEVEL! neq 0 (
    echo %RED%[ERROR]%RESET% Failed to install requirements.
    pause
    popd
    exit /b 1
)

echo %GREEN%[SUCCESS]%RESET% Environment ready.
pause
popd
exit /b 0