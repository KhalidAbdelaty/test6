#!/usr/bin/env python3
"""
Link Click Tracker
A Flask-based web application to track unique clicks on a specific URL.
Tracks visitors by IP address and provides analytics.
"""

from flask import Flask, request, redirect, render_template_string, jsonify
import json
import csv
import os
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# Configuration
TARGET_URL = "https://developer.huaweicloud.com/intl/en-us/activity/c64bd713260a42e7872e4138a2aef2db"
DATA_FILE = "click_data.json"
CSV_FILE = "click_data.csv"

def load_data():
    """Load existing click data from JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"clicks": []}
    return {"clicks": []}

def save_data(data):
    """Save click data to both JSON and CSV files."""
    # Save to JSON
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Save to CSV
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['IP Address', 'Timestamp', 'User Agent'])
        for click in data['clicks']:
            writer.writerow([click['ip'], click['timestamp'], click.get('user_agent', 'N/A')])

def get_client_ip():
    """Get the real IP address of the client, handling proxies."""
    if request.headers.get('X-Forwarded-For'):
        # Handle multiple IPs in X-Forwarded-For (first one is usually the real client)
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

@app.route('/track')
def track_click():
    """
    Main tracking route that logs the visitor and redirects to target URL.
    Only counts unique IPs once.
    """
    client_ip = get_client_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    timestamp = datetime.now().isoformat()
    
    # Load existing data
    data = load_data()
    
    # Check if this IP has already been recorded
    existing_ips = [click['ip'] for click in data['clicks']]
    
    if client_ip not in existing_ips:
        # New unique visitor - record the click
        click_record = {
            'ip': client_ip,
            'timestamp': timestamp,
            'user_agent': user_agent
        }
        data['clicks'].append(click_record)
        save_data(data)
        print(f"New unique visitor recorded: {client_ip} at {timestamp}")
    else:
        print(f"Returning visitor (not counted): {client_ip} at {timestamp}")
    
    # Redirect to target URL
    return redirect(TARGET_URL, code=302)

@app.route('/stats')
def show_stats():
    """Display statistics and visitor information."""
    data = load_data()
    total_unique = len(data['clicks'])
    
    # Create HTML template for stats page
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Link Click Statistics</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }
            .stats-box { background: #007acc; color: white; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center; }
            .stats-number { font-size: 2em; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f8f9fa; font-weight: bold; }
            tr:hover { background-color: #f5f5f5; }
            .refresh-btn { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 10px 0; }
            .refresh-btn:hover { background: #218838; }
            .tracking-url { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; word-break: break-all; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Link Click Statistics</h1>
            
            <div class="stats-box">
                <div class="stats-number">{{ total_unique }}</div>
                <div>Total Unique Visitors</div>
            </div>
            
            <h2>🔗 Your Tracking URL</h2>
            <div class="tracking-url">
                <strong>Share this link:</strong><br>
                {{ request.url_root }}track
            </div>
            
            <button class="refresh-btn" onclick="window.location.reload()">🔄 Refresh Stats</button>
            
            {% if clicks %}
            <h2>👥 Visitor Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>IP Address</th>
                        <th>First Visit</th>
                        <th>User Agent</th>
                    </tr>
                </thead>
                <tbody>
                    {% for click in clicks %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{ click.ip }}</td>
                        <td>{{ click.timestamp[:19].replace('T', ' ') }}</td>
                        <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">{{ click.user_agent }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p>No visitors yet. Share your tracking link to start collecting data!</p>
            {% endif %}
            
            <hr style="margin: 30px 0;">
            <p><small>
                <strong>Target URL:</strong> {{ target_url }}<br>
                <strong>Data files:</strong> {{ data_file }}, {{ csv_file }}
            </small></p>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(
        html_template,
        total_unique=total_unique,
        clicks=data['clicks'],
        target_url=TARGET_URL,
        data_file=DATA_FILE,
        csv_file=CSV_FILE
    )

@app.route('/api/stats')
def api_stats():
    """JSON API endpoint for statistics."""
    data = load_data()
    return jsonify({
        'total_unique_visitors': len(data['clicks']),
        'clicks': data['clicks'],
        'target_url': TARGET_URL
    })

@app.route('/')
def home():
    """Home page with instructions."""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Link Click Tracker</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; }
            .url-box { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 15px 0; word-break: break-all; }
            .btn { display: inline-block; padding: 10px 20px; margin: 10px 5px; text-decoration: none; border-radius: 5px; color: white; }
            .btn-primary { background: #007acc; }
            .btn-success { background: #28a745; }
            .btn:hover { opacity: 0.8; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔗 Link Click Tracker</h1>
            <p>Welcome to your link tracking system!</p>
            
            <h3>Your Tracking Link:</h3>
            <div class="url-box">
                {{ request.url_root }}track
            </div>
            
            <p><strong>How to use:</strong></p>
            <ol>
                <li>Share the tracking link above on LinkedIn or anywhere else</li>
                <li>When people click it, they'll be redirected to your target URL</li>
                <li>Each unique IP address is counted only once</li>
                <li>Check your statistics anytime using the button below</li>
            </ol>
            
            <a href="/stats" class="btn btn-primary">📊 View Statistics</a>
            <a href="/api/stats" class="btn btn-success">📋 JSON API</a>
            
            <hr style="margin: 30px 0;">
            <p><small>Target URL: {{ target_url }}</small></p>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_template, target_url=TARGET_URL)

if __name__ == '__main__':
    print("🚀 Link Click Tracker Starting...")
    print(f"📊 Stats will be available at: http://localhost:5000/stats")
    print(f"🔗 Share this tracking link: http://localhost:5000/track")
    print(f"🎯 Redirects to: {TARGET_URL}")
    print("=" * 60)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)