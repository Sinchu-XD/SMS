#!/bin/bash
set -e
cd "$(dirname "$0")"
pip install -r requirements.txt -q 2>&1
python bot.py
