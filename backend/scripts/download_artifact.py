#!/usr/bin/env python3
"""
Download/Copy Artifact Images
Utility script to copy generated images from the .gemini artifacts directory
to a more accessible location (Desktop by default).
"""

import shutil
import os
from pathlib import Path

def copy_artifact(source_path: str, destination_name: str = None, dest_dir: str = None):
    """
    Copy an artifact image to Desktop or specified directory.
    
    Args:
        source_path: Full path to the source image
        destination_name: Optional custom name for the destination file
        dest_dir: Optional destination directory (defaults to Desktop)
    """
    source = Path(source_path)
    
    if not source.exists():
        print(f"❌ Source file not found: {source_path}")
        return False
    
    # Default to Desktop
    if dest_dir is None:
        dest_dir = Path.home() / "Desktop"
    else:
        dest_dir = Path(dest_dir)
    
    # Use original filename if no custom name provided
    if destination_name is None:
        destination_name = source.name
    
    destination = dest_dir / destination_name
    
    try:
        shutil.copy2(source, destination)
        print(f"✅ Successfully copied to: {destination}")
        return True
    except Exception as e:
        print(f"❌ Error copying file: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python download_artifact.py <source_path> [destination_name] [dest_directory]")
        print("\nExample:")
        print("  python download_artifact.py /path/to/artifact.png")
        print("  python download_artifact.py /path/to/artifact.png my_chart.png")
        print("  python download_artifact.py /path/to/artifact.png my_chart.png ~/Documents")
        sys.exit(1)
    
    source = sys.argv[1]
    dest_name = sys.argv[2] if len(sys.argv) > 2 else None
    dest_directory = sys.argv[3] if len(sys.argv) > 3 else None
    
    copy_artifact(source, dest_name, dest_directory)
