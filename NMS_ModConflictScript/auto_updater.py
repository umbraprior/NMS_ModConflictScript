#!/usr/bin/env python3
"""
Auto Updater Script for NMS Mod Conflict Checker
Checks for updates from GitHub repository and downloads only changed files
"""

import sys
import json
import hashlib
import zipfile
import tempfile
import shutil
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import ssl

# GitHub repository information
REPO_OWNER = "umbraprior"
REPO_NAME = "NMS_ModConflictScript"
REPO_URL = f"https://github.com/{REPO_OWNER}/{REPO_NAME}"
API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
BRANCH = "main"

# Files to track for updates (relative to NMS_ModConflictScript folder)
TRACKED_FILES = [
    "check_conflicts.bat",
    "gamedata_finder.py",
    "json_extract.py", 
    "path_verifier.py",
    "simple_conflict_checker.py",
    "steam_finder.py",
    "auto_updater.py"
]

# Version file to track current state
VERSION_FILE = "version_info.json"


def get_file_hash(file_path):
    """Calculate SHA256 hash of a file"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except (FileNotFoundError, PermissionError):
        return None


def load_version_info():
    """Load current version information"""
    script_dir = Path(__file__).parent
    version_file_path = script_dir / VERSION_FILE
    
    if not version_file_path.exists():
        return {
            "last_commit": None,
            "file_hashes": {},
            "last_check": None
        }
    
    try:
        with open(version_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {
            "last_commit": None,
            "file_hashes": {},
            "last_check": None
        }


def save_version_info(version_info):
    """Save current version information"""
    script_dir = Path(__file__).parent
    version_file_path = script_dir / VERSION_FILE
    
    try:
        with open(version_file_path, 'w', encoding='utf-8') as f:
            json.dump(version_info, f, indent=2)
        return True
    except Exception:
        return False


def make_request(url, timeout=10):
    """Make HTTP request with error handling"""
    try:
        # Create SSL context that doesn't verify certificates (for compatibility)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        req = Request(url)
        req.add_header('User-Agent', 'NMS-ModConflictScript-AutoUpdater/1.0')
        
        with urlopen(req, timeout=timeout, context=context) as response:
            return response.read().decode('utf-8')
    except (URLError, HTTPError, ssl.SSLError) as e:
        raise Exception(f"Network request failed: {str(e)}")


def get_latest_commit():
    """Get latest commit information from GitHub API"""
    try:
        url = f"{API_BASE}/commits/{BRANCH}"
        response_text = make_request(url)
        commit_data = json.loads(response_text)
        
        return {
            "sha": commit_data["sha"],
            "message": commit_data["commit"]["message"].split('\n')[0],  # First line only
            "date": commit_data["commit"]["committer"]["date"],
            "author": commit_data["commit"]["author"]["name"]
        }
    except Exception as e:
        raise Exception(f"Failed to get commit info: {str(e)}")


def get_file_from_repo(file_path, commit_sha):
    """Download a specific file from GitHub repository"""
    try:
        # Use raw GitHub URL to download file contents
        url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{commit_sha}/NMS_ModConflictScript/{file_path}"
        return make_request(url)
    except Exception as e:
        raise Exception(f"Failed to download {file_path}: {str(e)}")


def check_for_updates():
    """Check if updates are available"""
    try:
        print("Checking for updates...")
        
        # Get current version info
        current_version = load_version_info()
        
        # Get latest commit
        latest_commit = get_latest_commit()
        
        # If we don't have a recorded commit or it's different, check files
        if current_version["last_commit"] != latest_commit["sha"]:
            return {
                "updates_available": True,
                "latest_commit": latest_commit,
                "current_commit": current_version["last_commit"]
            }
        else:
            return {
                "updates_available": False,
                "latest_commit": latest_commit,
                "current_commit": current_version["last_commit"]
            }
            
    except Exception as e:
        return {
            "error": True,
            "message": str(e)
        }


def get_changed_files(latest_commit_sha):
    """Determine which files have changed by comparing hashes"""
    script_dir = Path(__file__).parent
    current_version = load_version_info()
    changed_files = []
    
    for file_name in TRACKED_FILES:
        file_path = script_dir / file_name
        
        try:
            # Get file content from repository
            repo_content = get_file_from_repo(file_name, latest_commit_sha)
            repo_hash = hashlib.sha256(repo_content.encode('utf-8')).hexdigest()
            
            # Compare with local file hash
            local_hash = current_version["file_hashes"].get(file_name)
            if local_hash != repo_hash:
                changed_files.append({
                    "name": file_name,
                    "local_hash": local_hash,
                    "repo_hash": repo_hash,
                    "content": repo_content
                })
        except Exception as e:
            # If we can't get the file, consider it changed
            changed_files.append({
                "name": file_name,
                "error": str(e)
            })
    
    return changed_files


def backup_file(file_path):
    """Create backup of existing file"""
    if file_path.exists():
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        try:
            shutil.copy2(file_path, backup_path)
            return str(backup_path)
        except Exception:
            return None
    return None


def update_files(changed_files):
    """Update the changed files"""
    script_dir = Path(__file__).parent
    updated_files = []
    failed_files = []
    
    for file_info in changed_files:
        file_name = file_info["name"]
        file_path = script_dir / file_name
        
        if "error" in file_info:
            failed_files.append(f"{file_name}: {file_info['error']}")
            continue
        
        try:
            # Create backup
            backup_path = backup_file(file_path)
            
            # Write new content
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(file_info["content"])
            
            updated_files.append({
                "name": file_name,
                "backup": backup_path
            })
            
        except Exception as e:
            failed_files.append(f"{file_name}: {str(e)}")
    
    return updated_files, failed_files


def perform_update():
    """Perform the actual update process"""
    try:
        print("Starting update process...")
        
        # Check for updates
        update_check = check_for_updates()
        if "error" in update_check:
            return {
                "status": "error",
                "message": update_check["message"]
            }
        
        if not update_check["updates_available"]:
            return {
                "status": "up_to_date",
                "message": "No updates available"
            }
        
        latest_commit = update_check["latest_commit"]
        print(f"New version available: {latest_commit['sha'][:8]}")
        print(f"Commit: {latest_commit['message']}")
        print(f"Author: {latest_commit['author']}")
        print(f"Date: {latest_commit['date']}")
        
        # Get changed files
        print("\nChecking for file changes...")
        changed_files = get_changed_files(latest_commit["sha"])
        
        if not changed_files:
            print("No file changes detected.")
            # Still update version info
            current_version = load_version_info()
            current_version["last_commit"] = latest_commit["sha"]
            save_version_info(current_version)
            return {
                "status": "up_to_date",
                "message": "Repository updated but no file changes"
            }
        
        print(f"Found {len(changed_files)} changed files:")
        for file_info in changed_files:
            print(f"  - {file_info['name']}")
        
        # Update files
        print("\nUpdating files...")
        updated_files, failed_files = update_files(changed_files)
        
        # Update version info
        current_version = load_version_info()
        current_version["last_commit"] = latest_commit["sha"]
        
        # Update file hashes for successfully updated files
        for file_info in changed_files:
            if "repo_hash" in file_info:
                current_version["file_hashes"][file_info["name"]] = file_info["repo_hash"]
        
        current_version["last_check"] = latest_commit["date"]
        save_version_info(current_version)
        
        return {
            "status": "success",
            "updated_files": updated_files,
            "failed_files": failed_files,
            "commit_info": latest_commit
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def interactive_update():
    """Interactive update with user prompts"""
    print("=" * 70)
    print("NMS MOD CONFLICT CHECKER - AUTO UPDATER")
    print("=" * 70)
    print()
    
    # Check for updates
    update_check = check_for_updates()
    
    if "error" in update_check:
        print(f"Error checking for updates: {update_check['message']}")
        print("You can still use the current version of the tool.")
        return False
    
    if not update_check["updates_available"]:
        print("You have the latest version!")
        return False
    
    latest_commit = update_check["latest_commit"]
    print("Update Available!")
    print(f"Latest version: {latest_commit['sha'][:8]}")
    print(f"Commit message: {latest_commit['message']}")
    print(f"Author: {latest_commit['author']}")
    print(f"Date: {latest_commit['date']}")
    print()
    
    # Ask user if they want to update
    while True:
        choice = input("Do you want to update now? (Y/N): ").strip().upper()
        if choice in ['Y', 'YES']:
            break
        elif choice in ['N', 'NO']:
            print("Update skipped. You can run the updater again later.")
            return False
        else:
            print("Please enter Y or N.")
    
    # Perform update
    result = perform_update()
    
    if result["status"] == "error":
        print(f"\nUpdate failed: {result['message']}")
        return False
    elif result["status"] == "up_to_date":
        print(f"\n{result['message']}")
        return False
    else:
        print("\nUpdate completed successfully!")
        if result["updated_files"]:
            print("Updated files:")
            for file_info in result["updated_files"]:
                print(f"  ✓ {file_info['name']}")
                if file_info["backup"]:
                    print(f"    (backup: {file_info['backup']})")
        
        if result["failed_files"]:
            print("Failed to update:")
            for error in result["failed_files"]:
                print(f"  ✗ {error}")
        
        return True


def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            # Just check for updates, don't prompt
            result = check_for_updates()
            print(json.dumps(result, indent=2))
            return 0 if not result.get("error") else 1
        elif sys.argv[1] == "--update":
            # Force update without prompting
            result = perform_update()
            print(json.dumps(result, indent=2))
            return 0 if result["status"] != "error" else 1
    
    # Interactive mode
    try:
        updated = interactive_update()
        return 0
    except KeyboardInterrupt:
        print("\nUpdate cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
