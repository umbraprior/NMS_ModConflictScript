#!/usr/bin/env python3
"""
Simple No Man's Sky Mod Conflict Checker
Just shows which mods share the same files MBIN.
"""

import os
from pathlib import Path
from collections import defaultdict

def find_mod_conflicts(mods_dir):
    """Find files that exist in multiple mods"""
    mods_dir = Path(mods_dir)
    file_to_mods = defaultdict(list)  # file_path -> [mod_names]
    
    # Scan each mod directory
    for mod_dir in mods_dir.iterdir():
        if not mod_dir.is_dir():
            continue
            
        mod_name = mod_dir.name
        
        # Find all files in this mod
        for file_path in mod_dir.rglob('*'):
            if file_path.is_file():
                # Get relative path from mod root
                rel_path = file_path.relative_to(mod_dir)
                
                # Only check MBIN files
                if rel_path.suffix.lower() == '.mbin':
                    file_to_mods[str(rel_path)].append(mod_name)
    
    # Find conflicts
    conflicts = {file_path: mods for file_path, mods in file_to_mods.items() if len(mods) > 1}
    
    return conflicts

def main():
    import sys
    
    # Parse command line arguments
    mods_dir = Path("../GAMEDATA/MODS")  # default
    if len(sys.argv) >= 3 and sys.argv[1] == "--mods-dir":
        mods_dir = Path(sys.argv[2])
    
    if not mods_dir.exists():
        print(f"Error: Mods directory not found: {mods_dir}")
        return
    
    conflicts = find_mod_conflicts(mods_dir)
    
    # Write to both console and file
    output_lines = []
    output_lines.append("=" * 70)
    output_lines.append("MOD CONFLICT ANALYSIS REPORT")
    output_lines.append("=" * 70)
    
    if not conflicts:
        output_lines.append("No conflicts found! All mods modify different files.")
    else:
        # Analyze conflicts and mod count for summary
        total_affected_mods = set()
        
        for file_path, mods in conflicts.items():
            total_affected_mods.update(mods)
        
        total_mods = len([d for d in mods_dir.iterdir() if d.is_dir()])
        
        output_lines.append("SUMMARY:")
        output_lines.append(f"  Found {len(conflicts)} conflicting MBIN files")
        output_lines.append(f"  {len(total_affected_mods)} of your {total_mods} mods are involved")
        output_lines.append("")
        output_lines.append("CONFLICTS:")
        output_lines.append("")
        
        for i, (file_path, mods) in enumerate(sorted(conflicts.items()), 1):
            output_lines.append(f"[{i}] {file_path}")
            output_lines.append(f"    Conflicting mods:")
            for mod in mods:
                output_lines.append(f"      - {mod}")
            output_lines.append("-" * 70)
            output_lines.append("")
        
        output_lines.append("=" * 70)
    
    # Print to console
    print("\n" + "\n".join(output_lines))

if __name__ == "__main__":
    main()
