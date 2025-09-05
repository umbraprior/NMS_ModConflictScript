# No Man's Sky Mod Conflict Checker

A simple tool to detect conflicting files between No Man's Sky mods.

## What it does

Scans your No Man's Sky mods folder and identifies which mods have conflicting `.mbin` files. Generates a detailed report showing exactly which files conflict and which mods are affected.

## What it doesn't do

Edit your mod files
Manage the conflicts in any way

## Requirements

- [Python 3.6 or higher](https://www.python.org/downloads/)
- Windows (batch script)

## Installation

1. Download or clone this repository
2. Extract `NMS_ModConflictScript` to any folder
    a. Do not place it or the files within to the folder where your mods are located
    b. Never place your mod folders or files within this directory
3. Run `check_conflicts.bat`

## Features

- Auto-detects Steam installation and No Man's Sky location
- Interactive menu for different mod folder locations
- Detailed conflict reports with summary statistics
- Optional log file output
