"""
WSGI entry point for PythonAnywhere
Configure your web app to use this
"""

import sys
from pathlib import Path

# Add current directory to Python path
path = str(Path(__file__).parent)
if path not in sys.path:
    sys.path.insert(0, path)

# Import Flask app
from app import app

# This is what PythonAnywhere looks for
application = app
