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
    
    # Check if path exists
    if not path.exists():
        return {
            "status": "error",
            "error": "path_not_found",
            "message": "The specified path does not exist",
            "path": str(path)
        }
    
    # Check if it's a directory
    if not path.is_dir():
        return {
            "status": "error",
            "error": "not_directory",
            "message": "The specified path is not a directory",
            "path": str(path)
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
        elif mod_count > 10:
            result["note"] = f"Showing first 10 of {mod_count} mod folders"
            
        return result
        
    except PermissionError:
        return {
            "status": "error",
            "error": "permission_denied",
            "message": "Permission denied accessing the directory",
            "path": str(path)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": "unknown_error",
            "message": f"Error reading directory: {str(e)}",
            "path": str(path)
        }


def main():
    """Main function to verify MODS path"""
    if len(sys.argv) != 2:
        print(json.dumps({
            "status": "error",
            "error": "invalid_args",
            "message": "Usage: path_verifier.py <mods_path>"
        }))
        return 1
    
    mods_path = sys.argv[1]
    result = verify_mods_path(mods_path)
    print(json.dumps(result, indent=2))
    
    # Return appropriate exit code
    if result["status"] == "success":
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
