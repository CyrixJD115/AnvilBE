@echo off
REM Quick script to build the installer using Inno Setup
REM Updated to automatically sign installer to reduce false positives
cd /d "%~dp0"

echo ========================================
echo AutoBE Installer Builder
echo Optimized to reduce Windows Defender false positives
echo ========================================
echo.

REM If executable doesn't exist, build it first (prefers Python 3.12 for compatibility)
if not exist "dist\AutoBE.exe" (
    echo AutoBE.exe not found. Building it first...
    echo.
    call "%~dp0build_exe.bat"
    if not exist "dist\AutoBE.exe" (
        echo ERROR: Build failed. AutoBE.exe still not found.
        pause
        exit /b 1
    )
    echo.
)

REM Check if icon exists
if not exist "NEXBOX.ico" (
    echo ERROR: NEXBOX.ico not found!
    echo Installer branding requires this icon file.
    echo Add NEXBOX.ico to the project root before building.
    echo.
    pause
    exit /b 1
)

REM Warn if no background music files are present to bundle into installer
set "HAS_MUSIC="
for /f "delims=" %%F in ('dir /b /a:-d "music\*.ogg" "music\*.mp3" "music\*.wav" 2^>nul') do (
    set "HAS_MUSIC=1"
    goto :music_check_done
)
:music_check_done
if not defined HAS_MUSIC (
    echo WARNING: No .ogg, .mp3, or .wav files found in music\.
    echo Users will get the music folder, but no playable default track.
    echo.
)

REM Find Inno Setup Compiler
set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist %INNO_SETUP% (
    echo ERROR: Inno Setup not found at: %INNO_SETUP%
    echo.
    echo Please:
    echo   1. Install Inno Setup from: https://jrsoftware.org/isdl.php
    echo   2. Or update the path in this script if installed elsewhere
    echo.
    pause
    exit /b 1
)

echo Found Inno Setup Compiler
echo Building installer...
echo.

REM Compile the installer (check result immediately with goto - no variable expansion issues)
%INNO_SETUP% AutoSetup.iss
if errorlevel 1 goto inno_failed

echo.
echo ========================================
echo Installer created successfully!
echo ========================================
echo.
set "LATEST_SETUP="
for /f "delims=" %%I in ('dir /b /a:-d /o:-d "Installer\AutoBE_*_Setup.exe" 2^>nul') do (
    set "LATEST_SETUP=Installer\%%I"
    goto :show_setup_path
)
:show_setup_path
if defined LATEST_SETUP (
    echo Location: %LATEST_SETUP%
) else (
    echo Location: Installer\AutoBE_*_Setup.exe
)
echo.

REM Automatically attempt to sign the installer
echo Attempting to sign the installer automatically...
echo (This helps prevent false positives from Windows Defender)
echo.
REM Ensure certificate exists with code signing EKU
if not exist "%~dp0TheBedrockLab-SelfSigned.pfx" (
    echo Creating code signing certificate...
    powershell -Command "$cert = New-SelfSignedCertificate -DnsName 'TheBedrockLab' -CertStoreLocation 'Cert:\CurrentUser\My' -NotAfter (Get-Date).AddYears(10) -Type CodeSigningCert; $pwd = ConvertTo-SecureString 'MarriageWithVVS10162001' -AsPlainText -Force; Export-PfxCertificate -Cert $cert -FilePath '%~dp0TheBedrockLab-SelfSigned.pfx' -Password $pwd"
)
call SignAutoBeFiles.bat
if errorlevel 1 (
    echo.
    echo WARNING: Automatic signing failed or signtool not found.
    echo The installer was built but is not signed.
    echo You can sign it manually later using SignAutoBeFiles.bat
    echo.
    echo NOTE: Unsigned installers may trigger Windows Defender warnings.
    echo To reduce false positives, ensure the installer is properly signed.
) else (
    echo.
    echo Installer has been successfully signed!
)

echo.
echo ========================================
echo Build complete!
echo ========================================
goto end

:inno_failed
echo.
echo ERROR: Installer build failed.
echo Check the error messages above.
echo.

:end
pause
