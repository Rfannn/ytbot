#!/bin/bash
cd "$(dirname "$0")/.."
source venv/bin/activate
nohup uvicorn main:app --host 127.0.0.1 --port 8001 --workers 1 > bot.log 2>&1 &
echo "Bot started on port 8001, PID: $!"
