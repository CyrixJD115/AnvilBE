@echo off
setlocal EnableDelayedExpansion
REM Build script for AutoBE executable
REM Uses Python 3.12 only for release compatibility
cd /d "%~dp0"

echo ========================================
echo AutoBE Build Script
echo ========================================
echo Working dir: %CD%
echo.

REM Require Python 3.12 for release builds (3.13 caused DLL load issues on some user PCs)
py -3.12 --version >nul 2>&1
if !errorlevel! equ 0 (set "PY=py -3.12" & goto :py_ok)
echo ERROR: Python 3.12 is required for release builds.
echo Python 3.13 builds can fail on user PCs with python313.dll load errors.
echo Install from https://www.python.org/downloads/
goto :fail

:py_ok
echo Using: !PY!
!PY! --version
echo.

echo [1/5] Installing dependencies...
!PY! -m pip install -r requirements.txt -q 2>nul
if !errorlevel! neq 0 (
    echo WARNING: pip install failed - continue without pypresence if offline.
)
!PY! -m pip install pyinstaller -q 2>nul
echo.

echo [2/5] Preparing MUSIC_CREDITS.txt...
if not exist "MUSIC_CREDITS.txt" (
    if exist ".autobe\MUSIC_CREDITS.txt" (
        copy ".autobe\MUSIC_CREDITS.txt" "MUSIC_CREDITS.txt" >nul
    ) else (
        echo AutoBE - Background Music Credit > "MUSIC_CREDITS.txt"
        echo. >> "MUSIC_CREDITS.txt"
        echo https://www.youtube.com/watch?v=XCFz3Xwx70Q >> "MUSIC_CREDITS.txt"
    )
)
REM Warn if no audio in music folder - exe and installer will have no background music
set "HAS_MUSIC="
for /f "delims=" %%F in ('dir /b /a:-d "music\*.ogg" "music\*.mp3" "music\*.wav" 2^>nul') do (
    set "HAS_MUSIC=1"
    goto :music_check_done
)
:music_check_done
if not defined HAS_MUSIC (
    echo WARNING: No .ogg, .mp3, or .wav in music\ - add at least one file so installed users get background music.
)
echo.

echo [3/5] Cleaning previous build...
if exist "build" rmdir /s /q "build" 2>nul
if exist "dist\AutoBE.exe" del /q "dist\AutoBE.exe" 2>nul
echo.

echo [4/5] Building executable (this may take a few minutes)...
!PY! -m PyInstaller --clean --noconfirm AutoBE.spec
set "BUILD_OK=!errorlevel!"
if !BUILD_OK! neq 0 (
    echo ERROR: PyInstaller build failed with code !BUILD_OK!
    goto :fail
)
if not exist "dist\AutoBE.exe" (
    echo ERROR: dist\AutoBE.exe was not created.
    goto :fail
)
echo Build OK: dist\AutoBE.exe
echo.

echo [5/5] Signing executable...
REM Ensure certificate exists with code signing EKU
if not exist "%~dp0TheBedrockLab-SelfSigned.pfx" (
    echo Creating code signing certificate...
    powershell -Command "$cert = New-SelfSignedCertificate -DnsName 'TheBedrockLab' -CertStoreLocation 'Cert:\CurrentUser\My' -NotAfter (Get-Date).AddYears(10) -Type CodeSigningCert; $pwd = ConvertTo-SecureString 'MarriageWithVVS10162001' -AsPlainText -Force; Export-PfxCertificate -Cert $cert -FilePath '%~dp0TheBedrockLab-SelfSigned.pfx' -Password $pwd"
)
call "%~dp0SignAutoBeFiles.bat"
if !errorlevel! neq 0 (
    echo WARNING: Signing failed. Exe is built but unsigned.
)
echo.
echo ========================================
echo Build process completed.
echo ========================================
goto :end

:fail
echo.
pause
exit /b 1

:end
pause
endlocal
