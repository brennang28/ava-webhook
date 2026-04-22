#!/bin/bash

# Ava Job Webhook Setup Script

echo "--- Initializing Ava Job Webhook ---"

# 1. Create environment
echo "Initializing environment with uv..."
# uv handles environment implicitly or explicitly
if [ ! -d ".venv" ]; then
    uv venv
fi

# 2. Install dependencies
echo "Installing dependencies..."
uv sync

# 3. Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env from example..."
    cp .env.example .env
    echo "!!! IMPORTANT: Edit .env and add your WEBHOOK_URL !!!"
fi

# 4. Initialize Database
echo "Initializing database..."
source .venv/bin/activate
python3 -c "import sqlite3; conn = sqlite3.connect('jobs.db'); conn.execute('CREATE TABLE IF NOT EXISTS jobs (job_id TEXT PRIMARY KEY, title TEXT, company TEXT, date_found TIMESTAMP)'); conn.close()"

echo "--- Setup Complete ---"
echo "Next steps:"
echo "1. Deploy your Google Apps Script and get the Web App URL."
echo "2. Add the URL to the .env file."
echo "3. Run './run.sh' to start catching jobs!"
