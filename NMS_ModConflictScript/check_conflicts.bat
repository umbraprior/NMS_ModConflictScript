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

title No Man's Sky Mod Conflict Checker
cls

REM Show loading screen while checking for updates
echo !CYAN!===============================================================================!RESET!
echo !CYAN!                    NO MAN'S SKY MOD CONFLICT CHECKER!RESET!
echo !CYAN!===============================================================================!RESET!
echo.
echo !YELLOW!Initializing...!RESET!
echo.
echo !WHITE!• Checking for updates...!RESET!
echo.

REM Check for updates first
python auto_updater.py --check > temp_update_check.json 2>&1
set update_check_code=%errorlevel%

if %update_check_code%==0 (
    REM Parse update check result
    for /f "usebackq delims=" %%i in (`python json_extract.py temp_update_check.json updates_available`) do set "updates_available=%%i"
    del temp_update_check.json 2>nul
    
    if "!updates_available!"=="true" (
        REM Updates are available - prompt user
        echo !YELLOW!===============================================================================!RESET!
        echo !YELLOW!                             UPDATE AVAILABLE!RESET!
        echo !YELLOW!===============================================================================!RESET!
        echo.
        echo !GREEN!A new version of the NMS Mod Conflict Checker is available!!RESET!
        echo.
        set /p update_choice="Would you like to update now? (!GREEN!Y!RESET!/!RED!N!RESET!): "
        
        if /i "!update_choice!"=="Y" (
            echo.
            echo !CYAN!Running auto-updater...!RESET!
            echo.
            python auto_updater.py
            
            echo.
            echo !YELLOW!Press any key to continue...!RESET!
            pause >nul
        ) else (
            echo.
            timeout /t 2 >nul
        )
        cls
    )
) else (
    REM Update check failed, continue silently
    del temp_update_check.json 2>nul
)

:CHOOSE_SOURCE
echo !MAGENTA!===============================================================================!RESET!
echo !MAGENTA!                    NO MAN'S SKY MOD CONFLICT CHECKER!RESET!
echo !MAGENTA!===============================================================================!RESET!
echo.
echo !YELLOW!Where would you like to look for mods?!RESET!
echo.
echo !GREEN![1]!RESET! Auto-detect Steam installation
echo !CYAN![2]!RESET! Current directory
echo !BLUE![3]!RESET! Specify custom path
echo.
set /p choice="Enter your choice (!GREEN!1!RESET!, !CYAN!2!RESET!, or !BLUE!3!RESET!): "

if "%choice%"=="1" (
    cls
    goto STEAM_DETECT
)
if "%choice%"=="2" (
    cls
    goto CURRENT_DIR
)
if "%choice%"=="3" (
    cls
    goto CUSTOM_PATH
)

echo !RED!Invalid choice. Please try again.!RESET!
echo.
goto CHOOSE_SOURCE

:STEAM_DETECT
echo.

REM Call Python script to find Steam installation
python steam_finder.py > temp_steam_result.json 2>&1
set steam_exit_code=%errorlevel%

REM Parse the JSON result
if %steam_exit_code%==0 (
    REM Steam found with mods - extract mods_path from JSON
    for /f "usebackq delims=" %%i in (`python json_extract.py temp_steam_result.json mods_path`) do set "mods_path=%%i"
    del temp_steam_result.json 2>nul
    
    echo !GREEN!Found No Man's Sky with mods at: !YELLOW!!mods_path!!RESET!
    goto VERIFY_PATH
    
) else if %steam_exit_code%==2 (
    REM Steam found but no mods folder
    del temp_steam_result.json 2>nul
    goto STEAM_NO_MODS
    
) else (
    REM Steam not found or other error
    del temp_steam_result.json 2>nul
    echo !RED!Steam installation not found or No Man's Sky not located.!RESET!
    echo !YELLOW!Please choose option 3 to specify the path manually.!RESET!
    echo.
    pause
    cls
    goto CHOOSE_SOURCE
)

:STEAM_NO_MODS
echo !YELLOW!===============================================================================!RESET!
echo !YELLOW!                            NO MODS FOUND!RESET!
echo !YELLOW!===============================================================================!RESET!
echo.
echo !GREEN!No Man's Sky was found in your Steam library!RESET!, but !RED!there are no mods installed!RESET!.
echo The !CYAN!GAMEDATA\MODS!RESET! folder does not exist, which means no mods have been installed yet.
echo.
echo This conflict checker is designed to analyze existing mod installations.
echo.
echo What would you like to do?
echo.
echo !GREEN![1]!RESET! Specify a different MODS folder path manually
echo !RED![2]!RESET! Exit (install some mods first, then run this tool)
echo.
set /p no_mods_choice="Enter your choice (!GREEN!1!RESET! or !RED!2!RESET!): "

if "%no_mods_choice%"=="1" (
    cls
    goto CUSTOM_PATH
)
if "%no_mods_choice%"=="2" goto END

echo !RED!Invalid choice.!RESET! Please enter 1 or 2.
goto STEAM_NO_MODS

:CURRENT_DIR
echo.
echo Searching for GAMEDATA folder relative to script location...

REM Call Python script to find GAMEDATA directory
python gamedata_finder.py > temp_gamedata_result.json 2>&1
set gamedata_exit_code=%errorlevel%

if %gamedata_exit_code%==0 (
    REM GAMEDATA found - extract mods_path from JSON
    for /f "usebackq delims=" %%i in (`python json_extract.py temp_gamedata_result.json mods_path`) do set "mods_path=%%i"
    del temp_gamedata_result.json 2>nul
    
    echo !GREEN!Found GAMEDATA/MODS at: !CYAN!!mods_path!!RESET!
    cls
    goto VERIFY_PATH
    
) else (
    REM GAMEDATA not found in current directory structure
    del temp_gamedata_result.json 2>nul
    echo !RED!No GAMEDATA/MODS folder found relative to script location.!RESET!
    echo.
    echo What would you like to do?
    echo.
    echo !GREEN![1]!RESET! Try Steam auto-detection instead
    echo !BLUE![2]!RESET! Specify custom path manually
    echo !RED![3]!RESET! Exit
    echo.
    set /p no_gamedata_choice="Enter your choice (!GREEN!1!RESET!, !BLUE!2!RESET!, or !RED!3!RESET!): "
    
    if "%no_gamedata_choice%"=="1" (
        cls
        goto STEAM_DETECT
    )
    if "%no_gamedata_choice%"=="2" (
        cls
        goto CUSTOM_PATH
    )
    if "%no_gamedata_choice%"=="3" goto END
    
    echo !RED!Invalid choice. Please enter 1, 2, or 3.!RESET!
    goto CURRENT_DIR
)

:CUSTOM_PATH
echo.
set /p mods_path="Enter the full path to your MODS folder: "
if "%mods_path%"=="" goto CUSTOM_PATH

REM Remove quotes if user added them manually
set "mods_path=%mods_path:"=%"

REM Remove leading and trailing spaces
for /f "tokens=* delims= " %%i in ("%mods_path%") do set "mods_path=%%i"
for /l %%a in (1,1,31) do if "!mods_path:~-1!"==" " set "mods_path=!mods_path:~0,-1!"

:VERIFY_PATH
echo !YELLOW!===============================================================================!RESET!
echo !YELLOW!                              PATH VERIFICATION!RESET!
echo !YELLOW!===============================================================================!RESET!
echo Selected path: !CYAN!%mods_path%!RESET!
echo.

REM Call Python script to verify path and count mods
python path_verifier.py "%mods_path%" > temp_verify_result.json 2>&1
set verify_exit_code=%errorlevel%

if %verify_exit_code%==0 (
    REM Path verification successful - parse results
    for /f "usebackq delims=" %%i in (`python json_extract.py temp_verify_result.json mod_count`) do set "mod_count=%%i"
    del temp_verify_result.json 2>nul
    
    echo !BLUE!Mod folders found: !mod_count!!RESET!
    echo.
    
    if !mod_count!==0 (
        echo !RED!WARNING: No mod folders found in this directory!!RESET!
        echo Make sure this is the correct MODS folder.
        echo.
    )
    
) else (
    REM Path verification failed - show detailed error
    echo !RED!ERROR: Path verification failed!!RESET!
    echo.
    echo !YELLOW!Debug information:!RESET!
    type temp_verify_result.json 2>nul || echo No error details available
    del temp_verify_result.json 2>nul
    echo.
    echo !CYAN!Common issues:!RESET!
    echo - Path contains typos or doesn't exist
    echo - Path requires different permissions  
    echo - Path exists but contains no mod folders
    echo - Path contains special characters
    echo.
    echo !YELLOW!Please check the path and try again.!RESET!
    echo.
    pause
    cls
    goto CHOOSE_SOURCE
)

:CONFIRM_SCAN
echo Would you like to scan this directory for conflicts?
set /p confirm="Enter !GREEN!Y!RESET! to continue, !YELLOW!N!RESET! to choose different path, !RED!Q!RESET! to quit: "

if /i "%confirm%"=="Q" goto END
if /i "%confirm%"=="N" (
    cls
    goto CHOOSE_SOURCE
)
if /i "%confirm%"=="Y" (
    cls
    goto START_SCAN
)

echo !RED!Invalid input. Please enter Y, N, or Q.!RESET!
goto CONFIRM_SCAN

:START_SCAN
echo !YELLOW!===============================================================================!RESET!
echo !YELLOW!                              SCANNING MODS!RESET!
echo !YELLOW!===============================================================================!RESET!
echo.
echo Scanning !BLUE!%mod_count%!RESET! mod folders for conflicts...
echo This may take a moment...
echo.

python simple_conflict_checker.py --mods-dir "%mods_path%"

echo.
set /p save_log="!CYAN!Would you like to save these results to a log file?!RESET! (!GREEN!Y!RESET!/!RED!N!RESET!): "

if /i "%save_log%"=="Y" (
    echo.
    python simple_conflict_checker.py --mods-dir "%mods_path%" > mod_conflicts.log 2>&1
    echo !GREEN!Results saved to: !YELLOW!mod_conflicts.log!RESET!
    echo.
    
    if /i "!save_log!"=="Y" (
        start mod_conflicts.log
    )
)

:END
