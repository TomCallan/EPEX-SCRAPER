import sqlite3
import datetime
import os
from flask import Flask, render_template_string

app = Flask(__name__)

DB_PATH = "epex_metrics.db"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>EPEX Scraper Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: #fdfdfd; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #1a1a1a; margin-bottom: 5px; }
        .header { display: flex; justify-content: space-between; align-items: flex-end; padding-bottom: 20px; border-bottom: 1px solid #eaeaea; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); background: white; border-radius: 8px; overflow: hidden; }
        th, td { padding: 12px 15px; text-align: left; }
        th { background-color: #f8f9fa; color: #555; text-transform: uppercase; font-size: 0.85em; letter-spacing: 0.5px; border-bottom: 2px solid #eaeaea; }
        tr { border-bottom: 1px solid #eaeaea; }
        tr:last-child { border-bottom: none; }
        tr:hover { background-color: #f8f9fa; }
        .success { color: #10b981; font-weight: bold; }
        .failed { color: #ef4444; font-weight: bold; }
        .badge { background: #e0e7ff; color: #4338ca; padding: 4px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 500; }
        .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #eaeaea; }
        .card h3 { margin: 0 0 10px 0; color: #666; font-size: 0.9em; text-transform: uppercase; letter-spacing: 0.5px; }
        .card .value { font-size: 1.8em; font-weight: bold; color: #111; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>⚡ EPEX VPS Dashboard</h1>
                <p style="color: #666; margin: 0;">Lightweight External Monitoring</p>
            </div>
            <div>
                <span class="badge">Live as of: {{ now }}</span>
            </div>
        </div>

        <div class="summary-cards">
            <div class="card">
                <h3>Total Executions</h3>
                <div class="value">{{ total_runs }}</div>
            </div>
            <div class="card">
                <h3>Extracted Data Rows</h3>
                <div class="value">{{ "{:,}".format(total_rows) }}</div>
            </div>
            <div class="card">
                <h3>Cron Reliability</h3>
                <div class="value">{{ success_rate }}%</div>
            </div>
        </div>

        <h2>Cron Job History</h2>
        <table>
            <thead>
                <tr>
                    <th>Run ID</th>
                    <th>Start Timestamp</th>
                    <th>End Timestamp</th>
                    <th>Status</th>
                    <th>Rows</th>
                    <th>Size (Bytes)</th>
                    <th>Error Detail</th>
                </tr>
            </thead>
            <tbody>
                {% for run in runs %}
                <tr>
                    <td>#{{ run[0] }}</td>
                    <td>{{ run[2] }}</td>
                    <td>{{ run[3] or '-' }}</td>
                    <td class="{{ 'success' if run[4] == 'COMPLETED' else 'failed' }}">{{ run[4] }}</td>
                    <td>{{ run[5] or 0 }}</td>
                    <td>{{ run[6] or 0 }}</td>
                    <td style="color: #ef4444; font-size: 0.85em;">{{ run[9] or '' }}</td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="7" style="text-align: center; color: #888; padding: 30px;">
                        No history found. Ensure cron is running and the database 'epex_metrics.db' exists.
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

def get_stats():
    if not os.path.exists(DB_PATH):
        return 0, 0, 0, []
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Check if table exists
    c.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='runs'")
    if c.fetchone()[0] != 1:
        conn.close()
        return 0, 0, 0, []
        
    c.execute("SELECT COUNT(*) FROM runs")
    total_runs = c.fetchone()[0]
    
    c.execute("SELECT SUM(rows_extracted) FROM runs WHERE status='COMPLETED'")
    total_rows = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(*) FROM runs WHERE status='COMPLETED'")
    completed_runs = c.fetchone()[0]
    success_rate = round((completed_runs / total_runs * 100) if total_runs > 0 else 0, 1)
    
    c.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 50")
    runs = c.fetchall()
    
    conn.close()
    return total_runs, total_rows, success_rate, runs

@app.route("/")
def index():
    try:
        total_runs, total_rows, success_rate, runs = get_stats()
    except Exception as e:
        return f"<h3>Database Connection Error:</h3><p>{e}</p>"
        
    return render_template_string(
        HTML_TEMPLATE,
        total_runs=total_runs,
        total_rows=total_rows,
        success_rate=success_rate,
        runs=runs,
        now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

if __name__ == "__main__":
    # Host on 0.0.0.0 so it is accessible publicly from the VPS IP address
    app.run(host="0.0.0.0", port=80)
