# EPEX SPOT Scraper

This is a toolkit to scrape market results directly from the [EPEX SPOT](https://www.epexspot.com/en/market-results) energy exchange. Since EPEX uses complex JavaScript-rendered tables, this scraper uses Headless Chromium (Playwright) to reliably extract the data.

## Features

- **Config-Driven:** Manage all scraping arguments and schedules through a single `config.yaml` file.
- **Native VPS Scheduling:** Includes a setup script (`setup_cron.sh`) that reads your YAML config and automatically deploys the scraper to your native Linux cron daemon.
- **Combinatorial Scraping:** Provide multiple parameters (e.g., DE and FR, or Continuous and Auction). The scraper computes all combinations and extracts them in a single browser session.
- **Unified Dataframe:** The scraper merges data from multiple countries or modalities into a single CSV file inside the `data/` directory.
- **Lightweight Web Dashboard:** Host a fast, single-file Flask web server (`web_dashboard.py`) to monitor your database logs, view extracted row amounts, and monitor cron success rates externally from any browser.

## Installation

You will need Python 3.9 or newer.

1. Install the required Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install the Playwright Chromium binaries:
```bash
playwright install chromium
```

## Usage

### 1. Configuration (config.yaml)
Create or edit your `config.yaml` to set your desired EPEX parameters and scheduling frequency.

```yaml
# Run every 30 minutes
cron: "*/30 * * * *"

market_area: 
  - DE
  - FR
modality: 
  - Continuous
product: 
  - "30"
  - "60"
# CSVs will be saved to data/ automatically
```

### 2. VPS Automated Scheduling
To run the scraper securely in the background using the native Linux daemon, run the setup script:

```bash
chmod +x setup_cron.sh
./setup_cron.sh
```
Note: You can view the live stdout logs of the scheduled runs natively via `tail -f cron_scraper.log`.

### 3. Web Monitoring Dashboard
Deploy the included backend UI to view your statistics from any device. It runs directly on Port 80.

```bash
# Recommended to run inside tmux or systemctl for persistence
sudo python web_dashboard.py
```
Open your server's public IP address in any browser to view the generated EPEX Dashboard.

### 4. Manual Scraper Usage
If you just want to run a single scrape manually, you can use `scaper.py`. You can still pass in the YAML config, or override arguments directly using CLI flags:

```bash
# Run once using config defaults
python scaper.py --config config.yaml

# Run once ignoring config, using standard CLI flags
python scaper.py --market_area DE FR --modality Continuous --product 30
```
