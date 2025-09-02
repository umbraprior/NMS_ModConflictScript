#!/usr/bin/env python3
"""
GAMEDATA Finder Script - Intelligently locates GAMEDATA/MODS folder relative to script location
Searches upward and sideways in directory tree to find No Man's Sky installation
"""

import sys
import json
from pathlib import Path


def find_gamedata_from_current():
    """Find GAMEDATA/MODS folder relative to current script location"""
    script_dir = Path(__file__).parent.absolute()
    
    # Search patterns - look for these directory structures
    search_patterns = [
        # Direct relative paths from script location
        "../GAMEDATA/MODS",
        "../../GAMEDATA/MODS", 
        "../../../GAMEDATA/MODS",
        
        # Look in parent directories
        "../MODS",
        "../../MODS",
        
        # Look for No Man's Sky game structure
        "../No Man's Sky/GAMEDATA/MODS",
        "../../No Man's Sky/GAMEDATA/MODS",
        
        # Look in common game installation patterns
        "../steamapps/common/No Man's Sky/GAMEDATA/MODS",
        "../../steamapps/common/No Man's Sky/GAMEDATA/MODS",
        "../../../steamapps/common/No Man's Sky/GAMEDATA/MODS",
    ]
    
    for pattern in search_patterns:
        potential_path = script_dir / pattern
        try:
            resolved_path = potential_path.resolve()
            if resolved_path.exists() and resolved_path.is_dir():
                # Verify it looks like a MODS directory by checking for subdirectories
                subdirs = [item for item in resolved_path.iterdir() if item.is_dir()]
                if len(subdirs) > 0:  # Has at least some subdirectories
                    return str(resolved_path)
        except (OSError, RuntimeError):
            continue
    
    # Try searching upward in directory tree
    current_dir = script_dir
    max_levels = 5  # Don't search too far up
    
    for level in range(max_levels):
        # Look for GAMEDATA folder in current directory
        gamedata_path = current_dir / "GAMEDATA" / "MODS"
        if gamedata_path.exists() and gamedata_path.is_dir():
            return str(gamedata_path)
        
        # Look for No Man's Sky folder in current directory
        nms_path = current_dir / "No Man's Sky" / "GAMEDATA" / "MODS"
        if nms_path.exists() and nms_path.is_dir():
            return str(nms_path)
        
        # Move up one directory
        parent_dir = current_dir.parent
        if parent_dir == current_dir:  # Reached root
            break
        current_dir = parent_dir
    
    return None


def scan_directory_tree(base_path, target_name="MODS", max_depth=3):
    """Recursively scan directory tree looking for MODS folders"""
    base_path = Path(base_path)
    found_paths = []
    
    def _scan_recursive(path, depth):
        if depth > max_depth:
            return
        
        try:
            for item in path.iterdir():
                if not item.is_dir():
                    continue
                
                # Check if this is a MODS folder with contents
                if item.name == target_name:
                    subdirs = [sub for sub in item.iterdir() if sub.is_dir()]
                    if len(subdirs) > 0:
                        found_paths.append(str(item))
                        continue
                
                # Check if this is GAMEDATA folder
                if item.name == "GAMEDATA":
                    mods_path = item / "MODS"
                    if mods_path.exists() and mods_path.is_dir():
                        subdirs = [sub for sub in mods_path.iterdir() if sub.is_dir()]
                        if len(subdirs) > 0:
                            found_paths.append(str(mods_path))
                        continue
                
                # Recursively search subdirectories
                _scan_recursive(item, depth + 1)
                
        except (PermissionError, OSError):
            pass
    
    _scan_recursive(base_path, 0)
    return found_paths


def main():
    """Main function to find GAMEDATA/MODS directory"""
    # First try relative path detection
    gamedata_path = find_gamedata_from_current()
    
    if gamedata_path:
        # Verify the path and count mods
        path = Path(gamedata_path)
        try:
            mod_folders = [item for item in path.iterdir() if item.is_dir()]
            mod_count = len(mod_folders)
            
            print(json.dumps({
                "status": "success",
                "mods_path": str(path),
                "mod_count": mod_count,
                "detection_method": "relative_search"
            }))
            return 0
            
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "error": "access_denied",
                "message": f"Found path but cannot access: {str(e)}",
                "path": gamedata_path
            }))
            return 1
    
    # Try scanning current directory tree as fallback
    script_dir = Path(__file__).parent.absolute()
    found_paths = scan_directory_tree(script_dir)
    
    if found_paths:
        # Use the first found path
        best_path = found_paths[0]
        path = Path(best_path)
        
        try:
            mod_folders = [item for item in path.iterdir() if item.is_dir()]
            mod_count = len(mod_folders)
            
            print(json.dumps({
                "status": "success", 
                "mods_path": str(path),
                "mod_count": mod_count,
                "detection_method": "directory_scan",
                "all_found_paths": found_paths
            }))
            return 0
            
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "error": "access_denied", 
                "message": f"Found path but cannot access: {str(e)}",
                "path": best_path
            }))
            return 1
    
    # No GAMEDATA/MODS found
    print(json.dumps({
        "status": "error",
        "error": "gamedata_not_found",
        "message": "No GAMEDATA/MODS directory found relative to script location",
        "searched_from": str(script_dir)
    }))
    return 1


if __name__ == "__main__":
    sys.exit(main())
