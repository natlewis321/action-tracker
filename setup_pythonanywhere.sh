#!/bin/bash
# One-command setup for PythonAnywhere
# Usage: bash setup_pythonanywhere.sh

set -e

echo "=== Action Tracker Setup ==="
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install --user flask werkzeug fpdf2 openpyxl
echo ""

# Seed database
echo "Setting up database..."
cd ~/action-tracker
python3 seed.py
echo ""

# Get username
USERNAME=$(whoami)

echo "============================================"
echo "  Files ready! Now configure the web app:"
echo "============================================"
echo ""
echo "1. Go to the WEB tab on PythonAnywhere"
echo "2. Click 'Add a new web app'"
echo "3. Click Next (accept the domain)"
echo "4. Choose 'Manual configuration'"
echo "5. Choose Python 3.10"
echo "6. On the Web tab, set:"
echo "   Source code:       /home/$USERNAME/action-tracker"
echo "   Working directory: /home/$USERNAME/action-tracker"
echo ""
echo "7. Click the WSGI configuration file link"
echo "   DELETE everything in it, paste this:"
echo ""
echo "   import sys"
echo "   path = '/home/$USERNAME/action-tracker'"
echo "   if path not in sys.path:"
echo "       sys.path.insert(0, path)"
echo "   from app import create_app"
echo "   application = create_app()"
echo ""
echo "8. Click Save, then Reload the web app"
echo ""
echo "Your site: https://$USERNAME.pythonanywhere.com"
echo "Login: admin@local / admin"
echo "(Change the password immediately in Admin > Users)"
echo ""
