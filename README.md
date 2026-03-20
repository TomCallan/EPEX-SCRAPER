# EPEX SPOT Scraper & Monitoring Dashboard

This is a toolkit to scrape market results directly from the [EPEX SPOT](https://www.epexspot.com/en/market-results) energy exchange. Since EPEX uses complex JavaScript-rendered tables, this scraper uses Headless Chromium (Playwright) to reliably extract the data.

## Features

- **Config-Driven:** You can manage all scraping arguments and schedules through a single `config.yaml` file.
- **Platform-Agnostic Scheduling:** It includes a scheduling script (`scheduler.py`) that uses cron expressions and runs in the background on Windows, macOS, and Linux without needing native cron.
- **Combinatorial Scraping:** You can provide multiple parameters (e.g., DE and FR, or Continuous and Auction). The scraper computes all combinations and extracts them in a single browser session.
- **Unified Dataframe:** The scraper merges data from multiple countries or modalities into a single CSV file inside the `data/` directory.
- **Telemetry & Dashboard:** It logs metrics to a local SQLite database (`epex_metrics.db`), tracking active status, rows downloaded, and file sizes. There is also a Textual TUI dashboard to view metrics and explore the extracted data.

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

### 2. Automated Scheduling (Recommended)
Run the built-in scheduler to run your scraping jobs in the background:

```bash
python scheduler.py --config config.yaml
```
Note: The scheduler continuously updates `scheduler_status.json` with the countdown to the next run, which can be hooked into dashboards or external tools.

### 3. Manual Scraper Usage
If you just want to run a single scrape manually, you can use `scaper.py`. You can still pass in the YAML config, or override arguments directly using CLI flags:

```bash
# Run once using config defaults
python scaper.py --config config.yaml

# Run once ignoring config, using standard CLI flags
python scaper.py --market_area DE FR --modality Continuous --product 30
```

## Monitoring Dashboard

The toolkit includes a live terminal dashboard to view your scraping history and browse extracted tables.

**Run locally in terminal:**
```bash
python dashboard.py
```

**Run in your browser:**
You can broadcast the terminal UI securely to a local web browser using `textual-web`:
```bash
textual-web --run "python dashboard.py"
```
This generates a localhost link you can open to manage and explore your datasets directly in the browser.
