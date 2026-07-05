@echo off
REM Build script for AutoBE with PyArmor obfuscation
REM Uses Python 3.13 (or 3.12) and auto-installs requirements + PyInstaller
REM Updated to reduce Windows Defender false positives
cd /d "%~dp0"

echo ========================================
echo AutoBE Build Script with Obfuscation
echo Optimized to reduce Windows Defender false positives
echo ========================================
echo.

REM Use Python 3.13 for builds (pygame has wheels; 3.14 would require building from source)
py -3.13 --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY=py -3.13
    goto :py_ok
)
py -3.12 --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY=py -3.12
    goto :py_ok
)
echo ERROR: Python 3.12 or 3.13 is required to build AutoBE.
echo Install from https://www.python.org/downloads/
echo.
pause
exit /b 1

:py_ok
echo Using: %PY%
%PY% --version
echo.

REM Auto-install dependencies and PyInstaller
echo Installing/updating dependencies (requirements.txt + PyInstaller)...
%PY% -m pip install -r requirements.txt -q
%PY% -m pip install pyinstaller -q
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

REM Check if PyArmor is installed (optional)
%PY% -c "import pyarmor" 2>nul
if %ERRORLEVEL% neq 0 (
    echo WARNING: PyArmor is not installed. Obfuscation will be skipped.
    echo To install: %PY% -m pip install pyarmor
    echo.
    set USE_OBFUSCATION=0
) else (
    set USE_OBFUSCATION=1
)
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist\AutoBE.exe" del /q "dist\AutoBE.exe"
if exist "obfuscated" rmdir /s /q "obfuscated"
echo.

REM Obfuscate the source code if PyArmor is available
if %USE_OBFUSCATION%==1 (
    echo Obfuscating source code with PyArmor...
    %PY% -m pyarmor gen --enable-rft --enable-bcc --enable-jit --restrict AutoBE.py
    if %ERRORLEVEL% neq 0 (
        echo WARNING: Obfuscation failed, continuing with normal build...
        set USE_OBFUSCATION=0
    ) else (
        echo Obfuscation completed.
        echo.
        REM Update spec file to use obfuscated file
        REM Note: You'll need to manually update AutoBE.spec to point to obfuscated file
        echo NOTE: Please update AutoBE.spec to use the obfuscated file location
        pause
    )
)

REM Build the executable
echo Building executable with PyInstaller...
%PY% -m PyInstaller --clean --noconfirm AutoBE.spec
if %ERRORLEVEL% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo.

REM Check if executable was created
if not exist "dist\AutoBE.exe" (
    echo ERROR: Executable was not created!
    pause
    exit /b 1
)

echo Build completed successfully!
echo Executable location: dist\AutoBE.exe
echo.

REM Automatically attempt to sign the executable
echo Attempting to sign the executable automatically...
echo (This helps prevent false positives from Windows Defender)
echo.
call SignAutoBeFiles.bat
if %ERRORLEVEL% neq 0 (
    echo.
    echo WARNING: Automatic signing failed or signtool not found.
    echo The executable was built but is not signed.
    echo You can sign it manually later using SignAutoBeFiles.bat
    echo.
    echo NOTE: Unsigned executables may trigger Windows Defender warnings.
    echo To reduce false positives, ensure the executable is properly signed.
) else (
    echo.
    echo Executable has been successfully signed!
)

echo.
echo ========================================
echo Build process completed!
echo ========================================
pause
