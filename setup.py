#!/usr/bin/env python3
"""
Setup script to create the Python bot project structure
Run this to initialize the directory structure and files
"""

import os
import sys
from pathlib import Path

# Create base directory
base_dir = Path(r'c:\Users\Rfan\Documents\khashayardev-youtube-downloader-template-eaf0430\python_bot')
base_dir.mkdir(parents=True, exist_ok=True)

# Create subdirectories
(base_dir / 'temp_files').mkdir(exist_ok=True)

print(f"✅ Created: {base_dir}")
print(f"✅ Created: {base_dir / 'temp_files'}")
print(f"\nNext, run the file creation script...")
