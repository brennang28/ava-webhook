#!/bin/bash

# Ava Job Webhook Execution Script

# Change to the script's directory
cd "$(dirname "$0")"

# Run the watcher
echo "--- $(date): Running Ava Job Watcher ---"
PYTHONPATH=src ./.venv/bin/python3 -m ava_webhook.watcher
echo "--- Done ---"
