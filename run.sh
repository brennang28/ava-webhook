#!/bin/bash

# Ava Job Webhook Execution Script

# Change to the script's directory
cd "$(dirname "$0")"

# Run the watcher
echo "--- $(date): Running Ava Job Watcher ---"
./.venv/bin/python3 watcher.py
echo "--- Done ---"
