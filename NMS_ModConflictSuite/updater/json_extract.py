#!/usr/bin/env python3
"""
Simple JSON value extractor for batch files
Usage: python json_extract.py <json_file> <key>
"""

import sys
import json
from pathlib import Path

def main():
    if len(sys.argv) != 3:
        print("ERROR: Usage: json_extract.py <json_file> <key>")
        return 1
    
    json_file = sys.argv[1]
    key = sys.argv[2]
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if key in data:
            print(data[key])
            return 0
        else:
            print(f"ERROR: Key '{key}' not found in JSON")
            return 1
            
    except FileNotFoundError:
        print(f"ERROR: File '{json_file}' not found")
        return 1
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in file '{json_file}'")
        return 1
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
