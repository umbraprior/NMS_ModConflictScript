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
BRANCH = "rewrite"

# Files to track for updates (relative to NMS_ModConflictSuite folder)
TRACKED_FILES = [
    "run_mcs.bat",
    "conflict_checker/check_conflicts.bat",
    "finders/gamedata_finder.py",
    "finders/steam_finder.py",
    "conflict_checker/path_verifier.py",
    "conflict_checker/simple_conflict_checker.py",
    "updater/json_extract.py", 
    "updater/auto_updater.py"
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


def is_first_run(version_info=None):
    """Check if this is the first run (no commit hash recorded)"""
    if version_info is None:
        version_info = load_version_info()
    
    last_commit = version_info.get("last_commit")
    return last_commit is None or last_commit == "null"


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
        url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{commit_sha}/NMS_ModConflictSuite/{file_path}"
        return make_request(url)
    except Exception as e:
        raise Exception(f"Failed to download {file_path}: {str(e)}")


def check_for_updates(silent=False, include_integrity=False):
    """Check if updates are available and optionally check file integrity"""
    try:
        if not silent:
            print("Checking for updates...")
        
        # Get current version info
        current_version = load_version_info()
        
        # Get latest commit
        latest_commit = get_latest_commit()
        
        result = {
            "updates_available": False,
            "latest_commit": latest_commit,
            "current_commit": current_version["last_commit"]
        }
        
        # If we need to include integrity check or if commit changed, check files
        if include_integrity or current_version["last_commit"] != latest_commit["sha"]:
            changed_files = get_changed_files(latest_commit["sha"])
            missing_files = []
            corrupted_files = []
            updated_files = []
            
            # Check if this is first run (no stored commit hash)
            first_run = is_first_run(current_version)
            
            for file_info in changed_files:
                if "error" in file_info:
                    # Could be missing file or network error
                    base_dir = Path(__file__).parent.parent
                    file_path = base_dir / file_info["name"]
                    if not file_path.exists():
                        missing_files.append(file_info["name"])
                    else:
                        # On first run, don't treat existing files as corrupted
                        if not first_run:
                            corrupted_files.append(file_info["name"])
                elif file_info.get("current_hash") is None:
                    missing_files.append(file_info["name"])
                elif file_info.get("current_hash") != file_info.get("repo_hash"):
                    # Check if local file was modified from stored version
                    local_hash = file_info.get("local_hash")
                    current_hash = file_info.get("current_hash")
                    repo_hash = file_info.get("repo_hash")
                    
                    if not first_run and local_hash and current_hash != local_hash:
                        # File was modified locally = corruption
                        corrupted_files.append(file_info["name"])
                    elif current_version["last_commit"] == latest_commit["sha"]:
                        # Same repo version but different hash = corruption
                        corrupted_files.append(file_info["name"])
                    elif first_run:
                        # On first run, files that don't match repo are just "existing"
                        # Don't treat as corrupted or needing update unless missing
                        pass
                    else:
                        # Different repo version = update available
                        updated_files.append(file_info["name"])
            
            # Determine status
            critical_issues = len(missing_files) + len(corrupted_files)
            # On first run, only show updates available if there are actual missing files that need repair
            if first_run:
                has_updates = critical_issues > 0
            else:
                has_updates = len(updated_files) > 0 or current_version["last_commit"] != latest_commit["sha"]
            
            result.update({
                "updates_available": has_updates,
                "integrity_status": "critical" if critical_issues > 0 else "ok",
                "missing_files": missing_files,
                "corrupted_files": corrupted_files, 
                "updated_files": updated_files,
                "needs_repair": critical_issues > 0,
                "can_repair": True
            })
        else:
            result.update({
                "integrity_status": "ok",
                "missing_files": [],
                "corrupted_files": [],
                "updated_files": [],
                "needs_repair": False,
                "can_repair": True
            })
            
        return result
            
    except Exception as e:
        return {
            "error": True,
            "message": str(e),
            "updates_available": False,
            "integrity_status": "unknown",
            "needs_repair": False,
            "can_repair": False
        }


def get_current_file_hash(file_name):
    """Get hash of current local file"""
    # Get the base directory (NMS_ModConflictScript)
    base_dir = Path(__file__).parent.parent
    file_path = base_dir / file_name
    
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except (FileNotFoundError, PermissionError):
        return None


def get_changed_files(latest_commit_sha):
    """Determine which files have changed by comparing hashes"""
    current_version = load_version_info()
    changed_files = []
    
    for file_name in TRACKED_FILES:
        try:
            # Get file content from repository
            repo_content = get_file_from_repo(file_name, latest_commit_sha)
            repo_hash = hashlib.sha256(repo_content.encode('utf-8')).hexdigest()
            
            # Compare with local file hash
            local_hash = current_version["file_hashes"].get(file_name)
            current_file_hash = get_current_file_hash(file_name)
            
            # Consider file changed if:
            # 1. We don't have a recorded hash for it, OR
            # 2. The recorded hash doesn't match the repo hash, OR  
            # 3. The current file hash doesn't match the repo hash
            if (local_hash != repo_hash or 
                current_file_hash != repo_hash or 
                current_file_hash is None):
                changed_files.append({
                    "name": file_name,
                    "local_hash": local_hash,
                    "current_hash": current_file_hash,
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


def cleanup_backup_files(updated_files, keep_backups=False):
    """Clean up backup files after successful update"""
    if keep_backups:
        return
    
    cleaned_backups = []
    failed_cleanups = []
    
    for file_info in updated_files:
        backup_path = file_info.get("backup")
        if backup_path and Path(backup_path).exists():
            try:
                Path(backup_path).unlink()
                cleaned_backups.append(backup_path)
            except Exception as e:
                failed_cleanups.append(f"{backup_path}: {str(e)}")
    
    if cleaned_backups:
        print(f"Cleaned up {len(cleaned_backups)} backup files")
    if failed_cleanups:
        print("Failed to clean up some backup files:")
        for error in failed_cleanups:
            print(f"  ✗ {error}")
    
    return cleaned_backups, failed_cleanups


def update_files(changed_files):
    """Update the changed files"""
    base_dir = Path(__file__).parent.parent
    updated_files = []
    failed_files = []
    
    for file_info in changed_files:
        file_name = file_info["name"]
        file_path = base_dir / file_name
        
        if "error" in file_info:
            failed_files.append(f"{file_name}: {file_info['error']}")
            continue
        
        try:
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
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


def initialize_version_tracking(latest_commit_sha):
    """Initialize version tracking for first run"""
    current_version = load_version_info()
    
    # If this is first run, record current file hashes and commit
    if is_first_run(current_version):
        print("Initializing version tracking...")
        
        # Record current file hashes
        for file_name in TRACKED_FILES:
            current_hash = get_current_file_hash(file_name)
            if current_hash:
                current_version["file_hashes"][file_name] = current_hash
        
        # Record current commit
        current_version["last_commit"] = latest_commit_sha
        current_version["last_check"] = get_latest_commit()["date"]
        
        save_version_info(current_version)
        print("Version tracking initialized.")


def perform_update(keep_backups=False):
    """Perform the actual update process"""
    try:
        print("Starting update process...")
        
        # Check for updates
        update_check = check_for_updates(silent=False)
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
        
        # Clean up backup files after successful update (unless keep_backups is True)
        if not keep_backups:
            print("\nCleaning up backup files...")
            cleanup_backup_files(updated_files)
        else:
            print("\nBackup files preserved (--keep-backups was specified)")
        
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
    update_check = check_for_updates(silent=False)
    
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
    result = perform_update(keep_backups=False)  # Interactive mode defaults to cleaning backups
    
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
    # Check for --keep-backups flag
    keep_backups = "--keep-backups" in sys.argv
    if keep_backups:
        sys.argv.remove("--keep-backups")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--check":
            # Just check for updates, don't prompt (for raw output)
            result = check_for_updates(silent=True)
            print(json.dumps(result, indent=2))
            return 0 if not result.get("error") else 1
        elif sys.argv[1] == "--update":
            # Force update without prompting
            result = perform_update(keep_backups=keep_backups)
            print(json.dumps(result, indent=2))
            return 0 if result["status"] != "error" else 1
        elif sys.argv[1] == "--verify":
            # Check installation integrity (unified with update check)
            result = check_for_updates(silent=True, include_integrity=True)
            
            # If this is first run and no critical issues, initialize tracking
            if (result.get("integrity_status") == "ok" and is_first_run()):
                try:
                    latest_commit = get_latest_commit()
                    initialize_version_tracking(latest_commit["sha"])
                except Exception:
                    pass  # Ignore errors during initialization
            
            # Simplify output for batch file
            output = {
                "status": result.get("integrity_status", "unknown"),
                "needs_repair": result.get("needs_repair", False),
                "can_repair": result.get("can_repair", False),
                "missing_files": result.get("missing_files", []),
                "corrupted_files": result.get("corrupted_files", []),
                "updates_available": result.get("updates_available", False),
                "is_first_run": is_first_run()
            }
            
            print(json.dumps(output, indent=2))
            return 0 if result.get("integrity_status") != "critical" else 1
        elif sys.argv[1] == "--repair":
            # Repair installation by downloading missing/corrupted files
            try:
                print("Checking for missing or corrupted files...")
                result = check_for_updates(silent=False, include_integrity=True)
                
                if result.get("integrity_status") == "critical":
                    missing_files = result.get("missing_files", [])
                    corrupted_files = result.get("corrupted_files", [])
                    
                    if missing_files or corrupted_files:
                        print(f"Found {len(missing_files)} missing and {len(corrupted_files)} corrupted files")
                        
                        # Get latest commit
                        latest_commit = get_latest_commit()
                        
                        # Repair each missing/corrupted file
                        repaired_count = 0
                        failed_repairs = []
                        
                        for file_name in missing_files + corrupted_files:
                            try:
                                print(f"Repairing {file_name}...")
                                
                                # Download file content
                                file_content = get_file_from_repo(file_name, latest_commit["sha"])
                                
                                # Determine file path
                                base_dir = Path(__file__).parent.parent
                                file_path = base_dir / file_name
                                
                                # Create directory if needed
                                file_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                # Create backup if file exists
                                if file_path.exists():
                                    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                                    file_path.rename(backup_path)
                                    print(f"  Created backup: {backup_path}")
                                
                                # Write new content
                                with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                                    f.write(file_content)
                                
                                print(f"  ✓ Successfully repaired {file_name}")
                                repaired_count += 1
                                
                            except Exception as e:
                                print(f"  ✗ Failed to repair {file_name}: {str(e)}")
                                failed_repairs.append(file_name)
                        
                        print(f"\nRepair complete: {repaired_count} files repaired")
                        if failed_repairs:
                            print(f"Failed repairs: {', '.join(failed_repairs)}")
                            return 1
                        
                        # Update version info with current hashes
                        current_version = load_version_info()
                        current_version["last_commit"] = latest_commit["sha"]
                        for file_name in missing_files + corrupted_files:
                            if file_name not in failed_repairs:
                                current_hash = get_current_file_hash(file_name)
                                if current_hash:
                                    current_version["file_hashes"][file_name] = current_hash
                        save_version_info(current_version)
                        
                        # Clean up backup files created during repair (unless keep_backups is True)
                        if not keep_backups:
                            print("\nCleaning up backup files...")
                            repair_files = []
                            for file_name in missing_files + corrupted_files:
                                if file_name not in failed_repairs:
                                    base_dir = Path(__file__).parent.parent
                                    file_path = base_dir / file_name
                                    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                                    if backup_path.exists():
                                        repair_files.append({"backup": str(backup_path)})
                            
                            if repair_files:
                                cleanup_backup_files(repair_files)
                        else:
                            print("\nBackup files preserved (--keep-backups was specified)")
                        
                        return 0
                    else:
                        print("No files need repair.")
                        return 0
                else:
                    print("Installation is healthy - no repairs needed.")
                    return 0
                    
            except Exception as e:
                print(f"Error during repair: {str(e)}")
                return 1
    
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
