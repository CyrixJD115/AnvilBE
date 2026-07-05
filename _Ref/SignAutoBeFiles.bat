@echo off
REM Code signing script for AutoBE
REM IMPORTANT: Update paths and password before use!

echo ========================================
echo AutoBE Code Signing Script
echo ========================================
echo.

REM Find signtool.exe (try common locations)
set SIGNTOOL=

REM Try to find signtool.exe in Windows Kits directories
REM Check multiple possible SDK versions and architectures

REM First, check custom/Downloads location
if exist "C:\Users\thede\Downloads\Windows Kits\10\WindowsSDK\bin\*" (
    for /d %%i in ("C:\Users\thede\Downloads\Windows Kits\10\WindowsSDK\bin\*") do (
        if exist "%%i\x64\signtool.exe" (
            set SIGNTOOL="%%i\x64\signtool.exe"
            goto :found
        )
        if exist "%%i\x86\signtool.exe" (
            set SIGNTOOL="%%i\x86\signtool.exe"
            goto :found
        )
        if exist "%%i\signtool.exe" (
            set SIGNTOOL="%%i\signtool.exe"
            goto :found
        )
    )
)

REM Check standard Program Files location
if exist "C:\Program Files (x86)\Windows Kits\10\bin\*" (
    for /d %%i in ("C:\Program Files (x86)\Windows Kits\10\bin\*") do (
        if exist "%%i\x64\signtool.exe" (
            set SIGNTOOL="%%i\x64\signtool.exe"
            goto :found
        )
        if exist "%%i\x86\signtool.exe" (
            set SIGNTOOL="%%i\x86\signtool.exe"
            goto :found
        )
        if exist "%%i\signtool.exe" (
            set SIGNTOOL="%%i\signtool.exe"
            goto :found
        )
    )
)

REM Also check if it's directly in the WindowsSDK folder (various possible structures)
REM Check for versioned subdirectories
if exist "C:\Users\thede\Downloads\Windows Kits\10\WindowsSDK\bin\*" (
    for /d %%i in ("C:\Users\thede\Downloads\Windows Kits\10\WindowsSDK\bin\*") do (
        if exist "%%i\x64\signtool.exe" (
            set SIGNTOOL="%%i\x64\signtool.exe"
            goto :found
        )
        if exist "%%i\x86\signtool.exe" (
            set SIGNTOOL="%%i\x86\signtool.exe"
            goto :found
        )
        if exist "%%i\signtool.exe" (
            set SIGNTOOL="%%i\signtool.exe"
            goto :found
        )
    )
)

REM Check common alternative locations in Downloads
if exist "C:\Users\thede\Downloads\Windows Kits\10\bin\*" (
    for /d %%i in ("C:\Users\thede\Downloads\Windows Kits\10\bin\*") do (
        if exist "%%i\x64\signtool.exe" (
            set SIGNTOOL="%%i\x64\signtool.exe"
            goto :found
        )
        if exist "%%i\x86\signtool.exe" (
            set SIGNTOOL="%%i\x86\signtool.exe"
            goto :found
        )
    )
)

REM Try Visual Studio paths
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" (
    REM VS 2022 Community
    call "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" >nul 2>&1
    where signtool.exe >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        for /f "delims=" %%i in ('where signtool.exe') do set SIGNTOOL="%%i"
        goto :found
    )
)

REM Try specific version paths (check multiple common versions)
REM Version 10.0.26100.0 (newer)
if exist "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe" (
    set SIGNTOOL="C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe"
    goto :found
)
if exist "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x86\signtool.exe" (
    set SIGNTOOL="C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x86\signtool.exe"
    goto :found
)

REM Version 10.0.22621.0 (older)
if exist "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe" (
    set SIGNTOOL="C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
    goto :found
)
if exist "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x86\signtool.exe" (
    set SIGNTOOL="C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x86\signtool.exe"
    goto :found
)

REM Try Program Files x64 (generic)
if exist "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe" (
    set SIGNTOOL="C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe"
    goto :found
)

REM Try Program Files x86 (generic)
if exist "C:\Program Files (x86)\Windows Kits\10\bin\x86\signtool.exe" (
    set SIGNTOOL="C:\Program Files (x86)\Windows Kits\10\bin\x86\signtool.exe"
    goto :found
)

REM Try using where command (if in PATH)
where signtool.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "delims=" %%i in ('where signtool.exe') do set SIGNTOOL="%%i"
    goto :found
)

REM Not found - provide helpful instructions
echo ERROR: signtool.exe not found!
echo.
echo Searched locations:
echo   - C:\Program Files (x86)\Windows Kits\10\bin\*
echo   - C:\Users\thede\Downloads\Windows Kits\10\WindowsSDK\bin\*
echo   - Visual Studio paths
echo   - System PATH
echo.
echo ========================================
echo INSTALLATION REQUIRED
echo ========================================
echo.
echo You have installers in your Downloads folder:
echo.
echo OPTION 1 (EASIEST - Recommended):
echo   Run: C:\Users\thede\Downloads\ArtifactSigning.WindowsSignToolInstaller.exe
echo   This installs ONLY the signing tools (smaller, faster)
echo.
echo OPTION 2 (Full SDK):
echo   Run: C:\Users\thede\Downloads\winsdksetup.exe
echo   During installation, select "Windows SDK Signing Tools for Desktop Apps"
echo.
echo After installation:
echo   1. Close and reopen this command prompt
echo   2. Run SignAutoBeFiles.bat again
echo.
echo ========================================
echo.
echo To find signtool.exe after installation, run:
echo   find_signtool.bat
echo.
echo Or manually set the path in this script (see INSTALL_SIGNTOOL.md)
echo.
pause
exit /b 1

:found
echo Found signtool.exe at: %SIGNTOOL%
echo.

REM Certificate configuration - UPDATE THESE PATHS!
set CERTIFICATE="%~dp0TheBedrockLab-SelfSigned.pfx"
set PASSWORD=MarriageWithVVS10162001
set TIMESTAMP=http://timestamp.digicert.com

REM Verify certificate exists
if not exist %CERTIFICATE% (
    echo ERROR: Certificate file not found: %CERTIFICATE%
    echo Please update the CERTIFICATE path in this script.
    pause
    exit /b 1
)

REM Get script directory for relative paths
set SCRIPT_DIR=%~dp0

echo Signing the main application executable...
%SIGNTOOL% sign /f %CERTIFICATE% /p %PASSWORD% /tr %TIMESTAMP% /td sha256 /fd sha256 "%SCRIPT_DIR%dist\AutoBE.exe"
if errorlevel 1 goto :sign_exe_fallback1
goto :sign_exe_ok
:sign_exe_fallback1
echo First timestamp server failed, trying fallback...
%SIGNTOOL% sign /f %CERTIFICATE% /p %PASSWORD% /tr http://timestamp.sectigo.com /td sha256 /fd sha256 "%SCRIPT_DIR%dist\AutoBE.exe"
if errorlevel 1 goto :sign_exe_fallback2
goto :sign_exe_ok
:sign_exe_fallback2
echo Timestamp servers unreachable. Signing without timestamp...
%SIGNTOOL% sign /f %CERTIFICATE% /p %PASSWORD% /fd sha256 "%SCRIPT_DIR%dist\AutoBE.exe"
if errorlevel 1 goto :sign_exe_failed
:sign_exe_ok
echo Application executable successfully signed.
echo.

REM Sign installer if present
set "INSTALLER_EXE="
for /f "delims=" %%I in ('dir /b /a:-d /o:-d "%SCRIPT_DIR%Installer\AutoBE_*_Setup.exe" 2^>nul') do (
    set "INSTALLER_EXE=%SCRIPT_DIR%Installer\%%I"
    goto :installer_found
)
goto :no_installer
:installer_found
echo Signing the installer package...
echo Target installer: %INSTALLER_EXE%
%SIGNTOOL% sign /f %CERTIFICATE% /p %PASSWORD% /tr %TIMESTAMP% /td sha256 /fd sha256 "%INSTALLER_EXE%"
if errorlevel 1 %SIGNTOOL% sign /f %CERTIFICATE% /p %PASSWORD% /tr http://timestamp.sectigo.com /td sha256 /fd sha256 "%INSTALLER_EXE%"
if errorlevel 1 %SIGNTOOL% sign /f %CERTIFICATE% /p %PASSWORD% /fd sha256 "%INSTALLER_EXE%"
if errorlevel 1 goto :sign_installer_failed
echo Installer package successfully signed.
echo.
goto :verify_sigs
:no_installer
echo WARNING: Installer not found. Skipping installer signing.
echo.
goto :verify_sigs
:sign_exe_failed
echo ERROR: Failed to sign the application executable.
pause
exit /b 1
:sign_installer_failed
echo ERROR: Failed to sign the installer package.
pause
exit /b 1

:verify_sigs
echo Verifying signatures...
%SIGNTOOL% verify /pa "%SCRIPT_DIR%dist\AutoBE.exe"
if defined INSTALLER_EXE %SIGNTOOL% verify /pa "%INSTALLER_EXE%"
echo.
echo Signing process completed successfully!
pause