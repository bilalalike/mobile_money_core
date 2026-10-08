#!/bin/bash

echo "[*] Cleaning up old processes..."
pkill -f "python app.py" 2>/dev/null
pkill -f "ngrok http" 2>/dev/null
sleep 1

echo "[*] Starting Ngrok..."
ngrok http 5000 > /dev/null 2>&1 &
sleep 3

echo "[*] Updating .env with new Ngrok URL..."
source venv/bin/activate
python update_env.py

if [ $? -ne 0 ]; then
    echo "[!] Failed to update .env. Aborting."
    exit 1
fi

echo "[*] Starting Flask..."
python app.py
