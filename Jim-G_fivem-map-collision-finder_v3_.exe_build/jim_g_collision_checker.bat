@echo off
setlocal

ver >nul 2>nul
goto :check_vt
:check_vt
set _VT_OK=1
if not "%_VT_OK%"=="1" goto :no_vt
goto :set_colors
:no_vt
set ESC=
goto :set_colors

:set_colors
set ESC=
set RESET=%ESC%[0m
set BOLD=%ESC%[1m
set WHITE=%ESC%[37m
set YELLOW=%ESC%[33m
set GREEN=%ESC%[32m
set RED=%ESC%[31m
set BBLUE=%ESC%[44m
set BRED=%ESC%[41m
SET "PYTHON_SCRIPT=jim_g_collision_checker.py"
SET "OUTPUT_FILENAME=collision_report.html"


title Jim-G FiveM Collision Finder

cls
echo.
echo %BOLD%%BBLUE%%WHITE% ######################################### %RESET%
echo %BOLD%%BBLUE%%WHITE% #       Jim-G FiveM Collision Finder    # %RESET%
echo %BOLD%%BBLUE%%WHITE% ######################################### %RESET%
echo.
echo %WHITE%This tool scans a specified FiveM resource directory for%RESET%
echo %WHITE%filename conflicts among map-related files (e.g., .ymap, .ytd).%RESET%
echo %WHITE%Collisions can cause custom maps/MLOs to fail to load correctly.%RESET%
echo.

:GET_DIRECTORY
echo %BOLD%%YELLOW%===================================================================================%RESET%
SET "TARGET_DIR="
SET /P "TARGET_DIR=%BOLD%^> PASTE THE FULL PATH TO THE RESOURCES FOLDER HERE (e.g., ...\[mlo]): %RESET%"
echo %BOLD%%YELLOW%===================================================================================%RESET%
echo.

if "%TARGET_DIR%"=="" (
    echo %BOLD%%RED%[!] ERROR: The path cannot be empty. Please try again.%RESET%
    echo.
    goto GET_DIRECTORY
)

set "TARGET_DIR=%TARGET_DIR:"=%"

echo %BOLD%%WHITE%[INFO] Target Directory Set: "%TARGET_DIR%"%RESET%
echo %BOLD%%WHITE%[INFO] Output will be saved to: "%~dp0%OUTPUT_FILENAME%"%RESET%
echo.
echo %BOLD%%YELLOW%===================================================================================%RESET%
echo %BOLD%%YELLOW%                        STARTING INTERACTIVE CONFIGURATION...%RESET%
echo %BOLD%%YELLOW%===================================================================================%RESET%
echo.

python "%PYTHON_SCRIPT%" "%TARGET_DIR%" --output "%~dp0%OUTPUT_FILENAME%" --format html

echo.
echo %BOLD%%GREEN%===================================================================================%RESET%
echo %BOLD%%GREEN%                            SCAN COMPLETE!%RESET%
echo %BOLD%%GREEN%===================================================================================%RESET%
echo %BOLD%%GREEN%[SUCCESS] The full collision report has been generated in HTML format.%RESET%
echo %BOLD%%WHITE%[REPORT] Check "%~dp0%OUTPUT_FILENAME%" for details.%RESET%
echo.

pause
endlocal