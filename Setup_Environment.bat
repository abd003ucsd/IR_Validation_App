@echo off
setlocal

set ENV_DIR=env

if exist "%ENV_DIR%" (
    echo Environment already exists. Skipping creation.
) else (
    echo Creating environment...
    py -3 -m venv %ENV_DIR% >nul 2>&1
    if errorlevel 1 (
        python -m venv %ENV_DIR% >nul 2>&1
        if errorlevel 1 (
            echo Error: Python 3 was not found on your system.
            echo.
            echo Please download and install the latest version from:
            echo https://www.python.org/downloads/windows/
            echo.
            echo Important: During installation, make sure to check the box:
            echo "Add Python to PATH"
            echo.
            pause
            exit /b 1
        )    )
)

echo Upgrading pip...
"%ENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo Error: Failed to upgrade pip.
    pause
    exit /b 1
)

echo Installing requirements...
"%ENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install requirements.
    pause
    exit /b 1
)

echo Setup complete.
pause
exit /b 0