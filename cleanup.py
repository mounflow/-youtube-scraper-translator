#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup utility script.
Removes temporary files and directories created during development/testing.

Usage:
    python cleanup.py             # Interactive (asks before deleting)
    python cleanup.py --dry-run   # Show what would be deleted without deleting
    python cleanup.py --force     # Delete without prompting
"""

import sys
import glob
import argparse
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def find_temp_dirs() -> list:
    """Find all tmpclaude-*-cwd temporary directories."""
    return [Path(p) for p in glob.glob(str(PROJECT_ROOT / "tmpclaude-*-cwd"))]


def find_stale_files() -> list:
    """Find known stale/abnormal files in the project root."""
    stale_names = ["nul", "chrome", "=13.0.0"]
    found = []
    for name in stale_names:
        p = PROJECT_ROOT / name
        if p.exists():
            found.append(p)
    return found


def human_size(size_bytes: int) -> str:
    """Convert size in bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"


def get_size(path: Path) -> int:
    """Get total size of a file or directory in bytes."""
    if path.is_file():
        return path.stat().st_size
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except OSError:
                pass
    return total


def run_cleanup(dry_run: bool = False, force: bool = False) -> None:
    """Main cleanup routine."""
    temp_dirs = find_temp_dirs()
    stale_files = find_stale_files()
    targets = temp_dirs + stale_files

    if not targets:
        print("✅ Nothing to clean up.")
        return

    total_size = sum(get_size(t) for t in targets)
    print(f"Found {len(targets)} items to remove ({human_size(total_size)} total):")
    print()

    for t in targets:
        size = get_size(t)
        kind = "DIR " if t.is_dir() else "FILE"
        print(f"  [{kind}] {t.name:40s} {human_size(size):>10s}")

    print()

    if dry_run:
        print("⚠  Dry-run mode: no files were deleted.")
        return

    if not force:
        answer = input(f"Delete {len(targets)} items? [y/N]: ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return

    deleted = 0
    errors = 0
    for t in targets:
        try:
            if t.is_dir():
                shutil.rmtree(t)
            else:
                t.unlink()
            deleted += 1
        except Exception as e:
            print(f"  ❌ Failed to delete {t.name}: {e}")
            errors += 1

    print()
    print(f"✅ Deleted {deleted} items ({human_size(total_size)} freed).")
    if errors:
        print(f"⚠  {errors} items could not be deleted.")


def main():
    parser = argparse.ArgumentParser(description="Cleanup temp files in the project root")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    parser.add_argument("--force", action="store_true", help="Delete without prompting")
    args = parser.parse_args()

    run_cleanup(dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
