# EPEX SPOT Scraper & Monitoring Dashboard

A robust, enterprise-ready Python toolkit designed to scrape market results directly from the [EPEX SPOT](https://www.epexspot.com/en/market-results) energy exchange. It bypasses complex JavaScript-rendered tables using Headless Chromium via Playwright, and features a completely decoupled Weights & Biases (W&B) style terminal dashboard to monitor all your ongoing cron jobs, view extraction statistics, and explore CSV data.

## Features

- ⚡ **Playwright Engine:** Gracefully handles EPEX's dynamic JS loading and seamlessly extracts correct HTML datasets bypassing standard `requests` limitations.
- 🔀 **Combinatorial Scraping:** Supply multiple arguments for parameters like `--market_area DE FR` or `--modality Continuous Auction`. The scraper will dynamically compute all combinations and extract them via a single browser session concurrently.
- 📊 **Unified Dataframe:** Automatically stacks cross-country and cross-modality pulls into a single exported CSV file tagged with source-query context parameters.
- 📡 **Telemetry Logging:** Natively hooks into a local SQLite database (`epex_metrics.db`) to record active status, rows downloaded, MB sizes, start/end timestamps, and traceback exceptions.
- 🖥️ **Textual TUI Dashboard:** A real-time, terminal-based monitoring dashboard providing insight into metric key-performance indicators, cron expectations, live run history, and a built-in Data Explorer.

## Installation

Ensure you have Python 3.9+ installed.

1. Install the required Python packages:
```bash
pip install pandas playwright textual textual-web croniter
```

2. Install the Playwright Chromium binaries:
```bash
playwright install chromium
```

## 1. Using the Scraper (`scaper.py`)

The scraper operates completely independently and expects standard CLI interactions. It supports native OS cron job execution (Windows Task Scheduler, Linux Cron). 

To extract continuous trading results manually for France and Germany in a single sweep:

```bash
python scaper.py --market_area DE FR --modality Continuous
```

### Full Parameter List

*All parameters natively support passing multiple space-separated strings to auto-generate combinations!*

| Parameter | Default | Example |
| :--- | :--- | :--- |
| **`--market_area`** | `DE` | `--market_area DE FR GB` |
| **`--modality`** | `Continuous` | `--modality Continuous Auction` |
| **`--product`** | `30` | `--product 15 30 60` |
| **`--delivery_date`** | `2026-03-19` | `--delivery_date 2026-03-19 2026-03-20` |
| **`--auction`** | `""` |  |
| **`--trading_date`** | `""` |  |
| **`--output`** | *(Auto timestamp CSV)* | `--output epex_pull.csv` |

#### Telemetry Arguments

By passing telemetry variables, the scraper knows how to report itself to the Monitoring TUI.

```bash
python scaper.py --market_area DE --job_name "Daily Germany Pull" --cron_schedule "0 14 * * *"
```

- **`--job_name`**: Provides a clean name tag on the dashboard logs.
- **`--cron_schedule`**: Notifies the dashboard of its intended schedule via UNIX cron syntax, allowing the TUI to calculate the "Time Until Next Run" countdowns automatically.

## 2. Using the Monitoring TUI Dashboard (`dashboard.py`)

Run the monitoring dashboard directly from your terminal. It will watch `epex_metrics.db` and auto-refresh every few seconds.

```bash
python dashboard.py
```

### Textual-Web Integration 🌐

To access this dashboard beautifully formatted in your local web browser, you can proxy the command using `textual-web`:

```bash
textual-web --run "python dashboard.py"
```
It will output an `http://` localhost link that you can click to manage and explore your datasets directly in Chrome/Firefox.

### Dashboard Tabs
1. **W&B Overview Dashboard**: View aggregated MB downloaded and Total Rows sizes. Keep track of live Active Chron Jobs reporting, and see history of successful/failed data extractions.
2. **Data Explorer**: Instantly select and load previously generated CSV files natively in a fast Terminal/Browser Data Table rendering to view exactly what scripts have pulled.
