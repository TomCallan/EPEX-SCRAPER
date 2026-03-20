import argparse
import sys
import os
import time
import datetime
import itertools
import sqlite3
import pandas as pd
from io import StringIO
from playwright.sync_api import sync_playwright
import yaml

def scrape_epex_multiple(urls) -> list:
    """Scrape multiple EPEX SPOT market results pages using one Playwright browser session."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        for url_info in urls:
            url = url_info['url']
            print(f"Fetching URL: {url}")
            try:
                page.goto(url, wait_until="networkidle", timeout=60000)
                # Wait for main table using a relaxed selector
                page.wait_for_selector(".js-md-widget table", timeout=15000)
            except Exception as e:
                print(f"Warning: Could not load table for {url}. Error: {e}")
            
            html_content = page.content()
            results.append({
                'params': url_info['params'],
                'html': html_content
            })
            
        browser.close()
    return results

def parse_html_to_df(html_content: str) -> pd.DataFrame:
    """Parse output HTML into a pandas DataFrame."""
    try:
        dfs = pd.read_html(StringIO(html_content))
        if not dfs:
            return None
        
        target_df = None
        for df in dfs:
            clean_df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
            if len(clean_df.columns) > 1 and len(clean_df) > 1:
                target_df = clean_df
                break
                
        if target_df is None:
            target_df = dfs[0]
            
        return target_df
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="EPEX SPOT Market Results Scraper CLI")
    
    # Dashboard Telemetry args
    parser.add_argument("--job_name", default="Manual CLI Run", help="Dashboard: Name of the job execution")
    parser.add_argument("--cron_schedule", default="", help="Dashboard: Expected cron schedule for monitoring e.g '0 14 * * *'")
    
    # URL Parameters (support multiple values per arg)
    parser.add_argument("--market_area", nargs="+", default=["DE"], help="Market area (e.g., DE FR GB)")
    parser.add_argument("--auction", nargs="+", default=[""], help="Auction type")
    parser.add_argument("--trading_date", nargs="+", default=[""], help="Trading date (YYYY-MM-DD)")
    parser.add_argument("--delivery_date", nargs="+", default=["2026-03-19"], help="Delivery date (YYYY-MM-DD)")
    parser.add_argument("--underlying_year", nargs="+", default=[""], help="Underlying year")
    parser.add_argument("--modality", nargs="+", default=["Continuous"], help="Modality (e.g., Continuous Auction)")
    parser.add_argument("--sub_modality", nargs="+", default=[""], help="Sub modality")
    parser.add_argument("--technology", nargs="+", default=[""], help="Technology")
    parser.add_argument("--data_mode", nargs="+", default=["table"], help="Data mode (default: table)")
    parser.add_argument("--period", nargs="+", default=[""], help="Period")
    parser.add_argument("--production_period", nargs="+", default=[""], help="Production period")
    parser.add_argument("--product", nargs="+", default=["30"], help="Product (e.g., 15 30 60)")
    parser.add_argument("--output", default="", help="Optional CSV output file path prefix or directory (default: data/)")
    parser.add_argument("--config", default="", help="Path to YAML configuration file")
    
    args, remaining_argv = parser.parse_known_args()

    # Load from YAML config if provided
    if args.config:
        with open(args.config, "r") as f:
            config_data = yaml.safe_load(f) or {}
        # Update parser defaults with config
        parser.set_defaults(**config_data)
        # Re-parse to let command-line arguments override config values
        args = parser.parse_args()
    else:
        args = parser.parse_args()

    keys = [
        'market_area', 'auction', 'trading_date', 'delivery_date', 
        'underlying_year', 'modality', 'sub_modality', 'technology', 
        'data_mode', 'period', 'production_period', 'product'
    ]
    
    # Extract lists for each parameter to compute combinations
    param_lists = [getattr(args, k) if isinstance(getattr(args, k), list) else [getattr(args, k)] for k in keys]
    
    combinations = list(itertools.product(*param_lists))
    print("="*60)
    print(f"Starting Scraper - {len(combinations)} parameter combination(s) queued")
    print(f"Telemetry: Job Name='{args.job_name}', CronTarget='{args.cron_schedule}'")
    print("="*60)
    
    base_url = "https://www.epexspot.com/en/market-results"
    
    urls_to_scrape = []
    for combo in combinations:
        params_str_list = []
        param_dict = {}
        for i, key in enumerate(keys):
            val = combo[i]
            params_str_list.append(f"{key}={val}")
            param_dict[key] = val
        url = f"{base_url}?{'&'.join(params_str_list)}"
        urls_to_scrape.append({'url': url, 'params': param_dict})
    
    # Telemetry DB Connection
    start_time = datetime.datetime.now()
    conn, c, run_id = None, None, None
    try:
        conn = sqlite3.connect("epex_metrics.db", timeout=10.0)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT,
            start_time DATETIME,
            end_time DATETIME,
            status TEXT,
            rows_extracted INTEGER,
            file_size_bytes INTEGER,
            output_path TEXT,
            cron_schedule TEXT,
            error_message TEXT
        )''')
        c.execute('''INSERT INTO runs (job_name, start_time, status, cron_schedule)
                     VALUES (?, ?, ?, ?)''', (args.job_name, start_time.isoformat(), 'RUNNING', args.cron_schedule))
        run_id = c.lastrowid
        conn.commit()
    except Exception as db_e:
        print(f"Warning: Could not connect to monitoring DB: {db_e}")
    
    try:
        results = scrape_epex_multiple(urls_to_scrape)
        all_dfs = []
        
        for res in results:
            df = parse_html_to_df(res['html'])
            if df is not None:
                # Add context columns to differentiate rows when querying multiple areas/modalities
                for k, v in res['params'].items():
                    if v: # Add only active filters
                        df[f"query_{k}"] = v
                all_dfs.append(df)
        
        if all_dfs:
            final_df = pd.concat(all_dfs, ignore_index=True)
            print("\n--- Extracted Data Preview ---")
            print(final_df.head(15).to_string())
            print(f"...\nTotal rows: {len(final_df)}")
            
            # Determine output path, defaulting to a timestamp CSV
            output_path = args.output
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            if not output_path:
                output_path = os.path.join("data", f"epex_data_{timestamp}.csv")
            elif os.path.isdir(output_path):
                output_path = os.path.join(output_path, f"epex_data_{timestamp}.csv")
            
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                
            final_df.to_csv(output_path, index=False)
            print(f"\nSaved all combined results to {output_path}")
            
            if conn and run_id:
                end_time = datetime.datetime.now().isoformat()
                file_size = os.path.getsize(output_path)
                c.execute('''UPDATE runs SET end_time = ?, status = ?, rows_extracted = ?, file_size_bytes = ?, output_path = ? WHERE id = ?''',
                               (end_time, 'COMPLETED', len(final_df), file_size, output_path, run_id))
                conn.commit()
                conn.close()
                
        else:
            print("Failed to extract any data. Website structure may have changed, or data might not be available.")
            if conn and run_id:
                c.execute('''UPDATE runs SET end_time = ?, status = ?, error_message = ? WHERE id = ?''',
                               (datetime.datetime.now().isoformat(), 'FAILED', 'No tables found', run_id))
                conn.commit()
                conn.close()
            sys.exit(1)
            
    except Exception as e:
        if conn and run_id:
            c.execute('''UPDATE runs SET end_time = ?, status = ?, error_message = ? WHERE id = ?''',
                           (datetime.datetime.now().isoformat(), 'FAILED', str(e), run_id))
            conn.commit()
            conn.close()
        raise e

if __name__ == "__main__":
    main()