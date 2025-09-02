#!/usr/bin/env python3
"""
Path Verifier Script - Validates MODS folder paths and counts mod folders
Returns JSON with path validation results and mod folder count
"""

import sys
import json
from pathlib import Path


def verify_mods_path(mods_path):
    """Verify a MODS folder path and count mod folders"""
    path = Path(mods_path)
    
    # Debug info for troubleshooting
    debug_info = {
        "original_path": mods_path,
        "resolved_path": str(path.resolve()) if path.exists() else str(path),
        "parent_exists": path.parent.exists() if path.parent != path else False,
        "is_absolute": path.is_absolute()
    }
    
    # Check if path exists
    if not path.exists():
        return {
            "status": "error",
            "error": "path_not_found", 
            "message": f"The specified path does not exist: {path}",
            "path": str(path),
            "debug": debug_info
        }
    
    # Check if it's a directory
    if not path.is_dir():
        return {
            "status": "error",
            "error": "not_directory",
            "message": f"The specified path is not a directory: {path}",
            "path": str(path),
            "debug": debug_info
        }
    
    # Count mod folders (directories only)
    try:
        mod_folders = [item for item in path.iterdir() if item.is_dir()]
        mod_count = len(mod_folders)
        
        # Get list of mod folder names for display
        mod_names = [folder.name for folder in mod_folders]
        
        result = {
            "status": "success",
            "path": str(path),
            "mod_count": mod_count,
            "mod_folders": mod_names[:10],  # Limit to first 10 for display
            "total_folders": mod_count
        }
        
        if mod_count == 0:
            result["warning"] = "No mod folders found in this directory"
            result["debug"] = debug_info
        elif mod_count > 10:
            result["note"] = f"Showing first 10 of {mod_count} mod folders"
            
        return result
        
    except PermissionError:
        return {
            "status": "error",
            "error": "permission_denied",
            "message": "Permission denied accessing the directory",
            "path": str(path),
            "debug": debug_info
        }
    except Exception as e:
        return {
            "status": "error",
            "error": "unknown_error",
            "message": f"Error reading directory: {str(e)}",
            "path": str(path),
            "debug": debug_info
        }


def main():
    """Main function to verify MODS path"""
    # Debug: Show what arguments we actually received
    arg_debug = {
        "argc": len(sys.argv),
        "argv": sys.argv,
        "joined_args": " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    }
    
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "error": "no_args",
            "message": "Usage: path_verifier.py <mods_path>",
            "debug_args": arg_debug
        }))
        return 1
    elif len(sys.argv) > 2:
        # Multiple arguments might mean the path with spaces was split
        # Try joining them back together
        mods_path = " ".join(sys.argv[1:])
        # Write warning to stderr (won't interfere with JSON output)
        sys.stderr.write(f"WARNING: Multiple arguments detected, joining as single path: {mods_path}\n")
    else:
        mods_path = sys.argv[1]
    
    result = verify_mods_path(mods_path)
    # Add argument debugging to the result
    if result["status"] == "error":
        result["debug_args"] = arg_debug
    
    print(json.dumps(result, indent=2))
    
    # Return appropriate exit code
    if result["status"] == "success":
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
