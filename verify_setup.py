#!/usr/bin/env python3
"""
COPY THIS FILE TO YOUR PROJECT ROOT

This script helps organize your Python bot files for deployment.
Run it after uploading files to PythonAnywhere.
"""

import os
import sys
from pathlib import Path

def check_files():
    """Verify all required files are present"""
    required_files = [
        'app.py',
        'config.py',
        'database.py',
        'downloader.py',
        'bot_handler.py',
        'wsgi.py',
        'requirements.txt',
    ]
    
    print("🔍 Checking for required files...\n")
    
    missing = []
    found = []
    
    for file in required_files:
        if Path(file).exists():
            size = Path(file).stat().st_size
            print(f"✅ {file:<20} ({size:>6} bytes)")
            found.append(file)
        else:
            print(f"❌ {file:<20} (MISSING)")
            missing.append(file)
    
    print(f"\n📊 Summary: {len(found)}/{len(required_files)} files found")
    
    if missing:
        print(f"\n⚠️ Missing files: {', '.join(missing)}")
        print("\nPlease upload these files from the session workspace.")
        return False
    else:
        print("\n✅ All files present! Ready to deploy.")
        return True

def create_directories():
    """Create required directories"""
    print("\n📁 Creating required directories...\n")
    
    dirs = [
        'temp_files',
    ]
    
    for dir_name in dirs:
        path = Path(dir_name)
        if path.exists():
            print(f"✅ {dir_name}/ already exists")
        else:
            path.mkdir(exist_ok=True)
            print(f"✅ Created {dir_name}/")

def check_config():
    """Check if config has placeholders"""
    print("\n⚙️ Checking configuration...\n")
    
    try:
        with open('config.py', 'r') as f:
            content = f.read()
        
        if 'YOUR_BOT_TOKEN' in content:
            print("⚠️ BALE_BOT_TOKEN not configured")
            print("   Set in PythonAnywhere Web → Environment variables")
        else:
            print("✅ BALE_BOT_TOKEN looks configured")
        
        if 'YOUR_WEBHOOK_URL' in content:
            print("⚠️ WEBHOOK_URL not configured")
            print("   Set in PythonAnywhere Web → Environment variables")
        else:
            print("✅ WEBHOOK_URL looks configured")
            
    except FileNotFoundError:
        print("❌ config.py not found")

def print_next_steps():
    """Print next steps"""
    print("\n" + "="*60)
    print("📋 NEXT STEPS")
    print("="*60)
    
    steps = [
        "1. Verify all files are present (use this script)",
        "2. Set environment variables in PythonAnywhere:",
        "   - BALE_BOT_TOKEN (your bot token)",
        "   - WEBHOOK_URL (https://your-username.pythonanywhere.com/webhook)",
        "3. Create virtualenv: mkvirtualenv --python=/usr/bin/python3.10 youtube-dl",
        "4. Install dependencies: pip install -r requirements.txt",
        "5. Configure WSGI file (use content from wsgi.py)",
        "6. Reload web app in PythonAnywhere",
        "7. Set Bale webhook to your URL",
        "8. Test with /start command",
    ]
    
    for step in steps:
        print(step)
    
    print("\n" + "="*60)
    print("For detailed instructions, see DEPLOYMENT_GUIDE.md")
    print("="*60 + "\n")

def main():
    print("\n" + "🎬 BALE YOUTUBE DOWNLOADER - SETUP HELPER".center(60))
    print("="*60 + "\n")
    
    # Check files
    files_ok = check_files()
    
    # Create directories
    if files_ok:
        create_directories()
    
    # Check config
    check_config()
    
    # Print next steps
    print_next_steps()
    
    if files_ok:
        print("✅ Everything looks good! Follow the next steps to deploy.\n")
        return 0
    else:
        print("❌ Some files are missing. Please upload them first.\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
