@echo off
REM Run the signtool installer from Downloads

echo ========================================
echo Installing SignTool...
echo ========================================
echo.

set INSTALLER="C:\Users\thede\Downloads\signtool.bat"

if exist %INSTALLER% (
    echo Running installer: %INSTALLER%
    echo.
    echo This will install signtool.exe silently.
    echo Please wait...
    echo.
    call %INSTALLER%
    echo.
    echo ========================================
    echo Installation should be complete!
    echo ========================================
    echo.
    echo Next steps:
    echo   1. Wait a few seconds for installation to finish
    echo   2. Close this window
    echo   3. Run SignAutoBeFiles.bat again
    echo.
    echo Expected location:
    echo   C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe
    echo.
) else (
    echo ERROR: Installer not found at: %INSTALLER%
    echo.
    echo Please check that signtool.bat exists in your Downloads folder.
    echo.
)

timeout /t 10
pause
