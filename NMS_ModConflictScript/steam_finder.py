#!/usr/bin/env python3
"""
Steam Finder Script - Locates No Man's Sky installation in Steam libraries
Returns the MODS folder path if found, or appropriate error codes
"""

import sys
from pathlib import Path
import json
import string
import os
try:
    import winreg
except ImportError:
    winreg = None


def find_steam_from_registry():
    """Find Steam installation path from Windows registry"""
    if not winreg:
        return None
    
    # Registry keys where Steam installation path might be stored
    registry_keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam", "SteamPath"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam", "SteamExe"),
    ]
    
    for hkey, subkey, value_name in registry_keys:
        try:
            with winreg.OpenKey(hkey, subkey) as key:
                steam_path, _ = winreg.QueryValueEx(key, value_name)
                
                # Handle SteamExe case (points to steam.exe, we need the directory)
                if value_name == "SteamExe":
                    steam_path = str(Path(steam_path).parent)
                
                # Convert to Path object and verify
                steam_path = Path(steam_path)
                if steam_path.exists() and (steam_path / "steam.exe").exists():
                    return steam_path
                    
        except (FileNotFoundError, OSError, Exception):
            continue
    
    return None


def get_available_drives():
    """Get all available drive letters on Windows"""
    drives = []
    for letter in string.ascii_uppercase:
        drive_path = f"{letter}:\\"
        if os.path.exists(drive_path):
            drives.append(letter)
    return drives


def find_steam_fallback():
    """Fallback method: Find Steam installation directory by searching all drives"""
    drives = get_available_drives()
    
    # Common Steam installation paths to check on each drive
    steam_paths = [
        "Program Files/Steam",
        "Program Files (x86)/Steam", 
        "Steam",
        "Games/Steam",
    ]
    
    for drive in drives:
        for steam_path in steam_paths:
            full_path = Path(f"{drive}:/{steam_path}")
            if full_path.exists() and (full_path / "steam.exe").exists():
                return full_path
    
    return None


def find_steam_installation():
    """Find Steam installation directory using registry first, then fallback to drive search"""
    # Try registry first
    steam_path = find_steam_from_registry()
    if steam_path:
        return steam_path
    
    # Fallback to drive search if registry method fails
    return find_steam_fallback()


def parse_library_folders(steam_path):
    """Parse libraryfolders.vdf to get all Steam library paths"""
    library_paths = []
    
    # Try different locations for libraryfolders.vdf
    vdf_locations = [
        steam_path / "steamapps" / "libraryfolders.vdf",
        steam_path / "config" / "libraryfolders.vdf"
    ]
    
    library_vdf = None
    for vdf_path in vdf_locations:
        if vdf_path.exists():
            library_vdf = vdf_path
            break
    
    if not library_vdf:
        return library_paths
    
    try:
        with open(library_vdf, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Parse the VDF format to extract library paths
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if '"path"' in line.lower():
                # Extract the path value
                parts = line.split('"')
                if len(parts) >= 4:
                    path_value = parts[3]
                    # Clean up the path
                    path_value = path_value.replace('\\\\', '\\').replace('\\', '/')
                    if path_value and Path(path_value).exists():
                        library_paths.append(Path(path_value))
                        
    except Exception:
        pass  # Ignore parsing errors
    
    return library_paths


def find_nms_in_library(library_path):
    """Check if No Man's Sky exists in a Steam library"""
    manifest_path = library_path / "steamapps" / "appmanifest_275850.acf"
    if not manifest_path.exists():
        return None, "no_manifest"
    
    game_path = library_path / "steamapps" / "common" / "No Man's Sky"
    if not game_path.exists():
        return None, "no_game_folder"
    
    mods_path = game_path / "GAMEDATA" / "MODS"
    if not mods_path.exists():
        return str(game_path), "no_mods_folder"
    
    return str(mods_path), "found"


def main():
    """Main function to find No Man's Sky Steam installation"""
    # Find Steam installation
    steam_path = find_steam_installation()
    if not steam_path:
        print(json.dumps({
            "status": "error",
            "error": "steam_not_found",
            "message": "Steam installation not found in registry or common drive locations"
        }))
        return 1
    
    # Get all library paths (including main Steam directory)
    library_paths = [steam_path] + parse_library_folders(steam_path)
    
    # Search each library for No Man's Sky
    for library_path in library_paths:
        result_path, status = find_nms_in_library(library_path)
        
        if status == "found":
            print(json.dumps({
                "status": "success",
                "mods_path": result_path,
                "steam_path": str(steam_path),
                "library_path": str(library_path)
            }))
            return 0
        elif status == "no_mods_folder":
            print(json.dumps({
                "status": "no_mods",
                "game_path": result_path,
                "steam_path": str(steam_path),
                "library_path": str(library_path)
            }))
            return 2
    
    # No Man's Sky not found in any library
    print(json.dumps({
        "status": "error",
        "error": "nms_not_found",
        "message": "No Man's Sky not found in any Steam library",
        "steam_path": str(steam_path),
        "libraries_checked": [str(p) for p in library_paths]
    }))
    return 1


if __name__ == "__main__":
    sys.exit(main())
