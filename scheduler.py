import os
import sys
import time
import datetime
import subprocess
import yaml
import json
from croniter import croniter

def update_status_file(status_file, data):
    """Safely update the JSON status file via a temporary file."""
    try:
        temp_file = status_file + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=4)
        os.replace(temp_file, status_file)
    except Exception as e:
        print(f"Warning: Failed to update status file: {e}")

def run_job(config_yaml, cron_expr):
    """Run the scraper.py script using the provided config."""
    print(f"[{datetime.datetime.now().isoformat()}] Starting scheduled scraper job...")
    cmd = [
        sys.executable, 
        "scaper.py", 
        "--config", config_yaml, 
        "--cron_schedule", cron_expr, 
        "--job_name", "Scheduled run"
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"[{datetime.datetime.now().isoformat()}] Job completed successfully.\n")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.datetime.now().isoformat()}] Job failed with exit code {e.returncode}.\n")

def main():
    import argparse
    parser = argparse.ArgumentParser("Scraper Scheduler")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml which contains 'cron' and scraper parameters")
    parser.add_argument("--status-file", default="scheduler_status.json", help="Path to write the scheduler status JSON for background polling")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Error: Config file '{args.config}' not found.")
        print("Please create one. Example:\n\ncron: '0 * * * *'\nmarket_area:\n  - DE\ndelivery_date:\n  - 2026-03-20")
        sys.exit(1)

    print(f"Loaded config from '{args.config}'. Status will be written to '{args.status_file}'.")
    print("Press Ctrl+C to exit.")

    while True:
        # Reload config every cycle so that changes are picked up dynamically
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f) or {}
            
        cron_expr = config.get('cron', "0 * * * *") # default every hour
        
        now = datetime.datetime.now()
        try:
            iter = croniter(cron_expr, now)
            next_run = iter.get_next(datetime.datetime)
        except Exception as e:
            print(f"Error parsing cron expression '{cron_expr}': {e}")
            sys.exit(1)
            
        print(f"[{now.isoformat()}] Next run scheduled at {next_run.isoformat()} based on cron '{cron_expr}'")
        
        # Sleep loop: update status file periodically
        while True:
            current_time = datetime.datetime.now()
            time_until = (next_run - current_time).total_seconds()
            
            if time_until <= 0:
                break
            
            status_data = {
                "current_time": current_time.isoformat(),
                "next_run_time": next_run.isoformat(),
                "seconds_until_next_run": round(time_until, 2),
                "cron_schedule": cron_expr,
                "status": "waiting"
            }
            update_status_file(args.status_file, status_data)
            
            # Wake up every 5 seconds to update the status file
            sleep_duration = min(5.0, time_until)
            time.sleep(sleep_duration)
            
        # It's time to run the job
        status_data = {
            "current_time": datetime.datetime.now().isoformat(),
            "next_run_time": next_run.isoformat(),
            "seconds_until_next_run": 0.0,
            "cron_schedule": cron_expr,
            "status": "running"
        }
        update_status_file(args.status_file, status_data)
        
        run_job(args.config, cron_expr)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting schedule scraper...")
