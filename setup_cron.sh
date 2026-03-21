#!/bin/bash
# EPEX SPOT Scraper native cron install script

echo "Reading cron configuration from config.yaml..."

# Safely extract cron from YAML natively using Python
CRON_EXPR=$(python3 -c "import yaml; print(yaml.safe_load(open('config.yaml', 'r')).get('cron', '0 * * * *'))" 2>/dev/null)

if [ -z "$CRON_EXPR" ]; then
    echo "Error parsing config.yaml"
    exit 1
fi

# Get absolute paths to run cron robustly
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PYTHON_BIN="$(command -v python3)"

if [ -z "$PYTHON_BIN" ]; then
    echo "Python3 not found! Please install it first."
    exit 1
fi

# Build cron command: cd to dir, execute python natively, dump logs
CRON_JOB="$CRON_EXPR cd \"$SCRIPT_DIR\" && $PYTHON_BIN scaper.py --config config.yaml >> \"$SCRIPT_DIR/cron_scraper.log\" 2>&1"

echo "Applying cron job:"
echo "  $CRON_JOB"

# Backup existing cron, safely remove any previous scaper.py crons, and append the new one
(crontab -l 2>/dev/null | grep -F -v "scaper.py --config config.yaml"; echo "$CRON_JOB") | crontab -

echo ""
echo "Success! The scraper has been scheduled on the native Linux cron daemon."
echo "View its execution output locally via: tail -f cron_scraper.log"
