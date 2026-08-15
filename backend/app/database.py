import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "stock_data.db"

def init_db():
    """Initialize database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS recommendations
                 (id INTEGER PRIMARY KEY,
                  ticker TEXT UNIQUE,
                  action TEXT,
                  score REAL,
                  reasons TEXT,
                  technical_signals TEXT,
                  created_at TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS stock_analysis
                 (id INTEGER PRIMARY KEY,
                  ticker TEXT UNIQUE,
                  data TEXT,
                  created_at TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS watchlist
                 (id INTEGER PRIMARY KEY,
                  ticker TEXT UNIQUE,
                  added_at TIMESTAMP)''')

    conn.commit()
    conn.close()


def cache_analysis(ticker, data):
    """Cache stock analysis data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO stock_analysis
                 (ticker, data, created_at)
                 VALUES (?, ?, ?)''',
              (ticker, json.dumps(data), datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_cached_analysis(ticker, max_age_minutes=5):
    """Get cached analysis if it hasn't expired"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT data, created_at FROM stock_analysis WHERE ticker = ?', (ticker,))
    row = c.fetchone()
    conn.close()

    if row:
        data_str, created_at_str = row
        try:
            created_at = datetime.fromisoformat(created_at_str)
            age_minutes = (datetime.now() - created_at).total_seconds() / 60
            if age_minutes <= max_age_minutes:
                return json.loads(data_str)
        except Exception:
            pass

    return None