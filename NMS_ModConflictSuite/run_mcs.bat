@echo off
setlocal enabledelayedexpansion

REM Enable ANSI color support  
for /f "delims=" %%A in ('echo prompt $E^| cmd') do set "ESC=%%A"

REM Define color codes for better visual presentation
set "RESET=%ESC%[0m"
set "BOLD=%ESC%[1m"
set "RED=%ESC%[91m"
set "GREEN=%ESC%[92m"
set "YELLOW=%ESC%[93m"
set "BLUE=%ESC%[94m"
set "MAGENTA=%ESC%[95m"
set "CYAN=%ESC%[96m"
set "WHITE=%ESC%[97m"

title No Man's Sky Mod Conflict Suite
cls

REM Show loading screen while initializing
echo !CYAN!===============================================================================!RESET!
echo !CYAN!                  NO MAN'S SKY MOD CONFLICT SUITE!RESET!
echo !CYAN!===============================================================================!RESET!
echo.
echo !YELLOW!Initializing...!RESET!
echo.
echo Checking for updates and verifying integrity...

REM Check for updates and verify integrity in one step
python updater\auto_updater.py --verify > temp_update_check.json 2>&1
set update_check_code=%errorlevel%

if %update_check_code%==1 (
    REM Critical integrity issues found
    cls
    echo !RED!===============================================================================!RESET!
    echo !RED!                          INSTALLATION CORRUPTED!RESET!
    echo !RED!===============================================================================!RESET!
    echo.
    echo !YELLOW!Critical issues were found with your installation files!!RESET!
    echo Some script files are missing or corrupted and need to be repaired.
    echo.
    
    set /p repair_choice="Would you like to repair them now? (!GREEN!Y!RESET!/!RED!N!RESET!): "
    
    if /i "!repair_choice!"=="Y" (
        echo.
        echo !CYAN!Repairing installation...!RESET!
        echo.
        python updater\auto_updater.py --repair
        echo.
        echo !YELLOW!Press any key to continue...!RESET!
        pause >nul
        cls
        
        REM Re-check after repair
        python updater\auto_updater.py --check > temp_update_check.json 2>&1
        set update_check_code=%errorlevel%
    ) else (
        echo.
        echo !RED!Cannot continue with corrupted installation.!RESET!
        echo !YELLOW!Please repair the installation or re-download the script.!RESET!
        echo.
        pause
        goto END
    )
)

REM Clear loading screen
cls

if %update_check_code%==0 (
    REM Parse update check result
    for /f "usebackq delims=" %%i in (`python updater\json_extract.py temp_update_check.json updates_available`) do set "updates_available=%%i"
    del temp_update_check.json 2>nul
    
    if "!updates_available!"=="true" (
        REM Updates are available - prompt user
        echo !YELLOW!===============================================================================!RESET!
        echo !YELLOW!                             UPDATE AVAILABLE!RESET!
        echo !YELLOW!===============================================================================!RESET!
        echo.
        echo !GREEN!A new version of the NMS Mod Conflict Suite is available!!RESET!
        echo.
        set /p update_choice="Would you like to update now? (!GREEN!Y!RESET!/!RED!N!RESET!): "
        
        if /i "!update_choice!"=="Y" (
            echo.
            echo !CYAN!Running auto-updater...!RESET!
            echo.
            python updater\auto_updater.py
            
            echo.
            echo !YELLOW!Press any key to continue...!RESET!
            pause >nul
            cls
        ) else (
            echo.
            echo !YELLOW!Update skipped.!RESET!
            timeout /t 2 >nul
            cls
        )
    )
) else (
    REM Update check failed, continue silently
    del temp_update_check.json 2>nul
)

:MAIN_MENU
echo !MAGENTA!===============================================================================!RESET!
echo !MAGENTA!                  NO MAN'S SKY MOD CONFLICT SUITE!RESET!
echo !MAGENTA!===============================================================================!RESET!
echo.
echo !YELLOW!Welcome! Select a tool to use:!RESET!
echo.
echo !GREEN![1]!RESET! Mod Conflict Checker
echo !CYAN![2]!RESET! Additional Tools !YELLOW!(Coming Soon)!RESET!
echo !RED![0]!RESET! Exit
echo.
set /p tool_choice="Enter your choice (!GREEN!1!RESET!, !CYAN!2!RESET!, or !RED!0!RESET!): "

if "%tool_choice%"=="1" (
    cls
    goto RUN_CONFLICT_CHECKER
)
if "%tool_choice%"=="2" (
    echo.
    echo !YELLOW!Additional tools are planned for future releases!!RESET!
    echo !CYAN!Stay tuned for more mod management utilities.!RESET!
    echo.
    pause
    cls
    goto MAIN_MENU
)
if "%tool_choice%"=="0" goto END

echo !RED!Invalid choice. Please try again.!RESET!
echo.
timeout /t 2 >nul
cls
goto MAIN_MENU

:RUN_CONFLICT_CHECKER
echo !CYAN!===============================================================================!RESET!
echo !CYAN!                      LAUNCHING MOD CONFLICT CHECKER!RESET!
echo !CYAN!===============================================================================!RESET!
echo.
echo !YELLOW!Starting Mod Conflict Checker...!RESET!
echo.

REM Run the conflict checker
call conflict_checker\check_conflicts.bat
echo .
cls

:END
