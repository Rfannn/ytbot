#!/bin/bash
set -e

echo "=== YouTubeBot Setup for HestiaCP ==="

cd "$(dirname "$0")/.."

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
echo ""
echo "=== IMPORTANT ==="
echo "Edit the .env file with your actual credentials:"
echo "  nano .env"
echo ""
echo "Then run: bash deploy/start.sh"
echo ""
echo "To set the webhook, visit:"
echo "  https://your-domain.com/set-webhook"
