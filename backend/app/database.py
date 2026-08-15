import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "stock_data.db"

def init_db():
    """Initialize database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Recommendations table
    c.execute('''CREATE TABLE IF NOT EXISTS recommendations
                 (id INTEGER PRIMARY KEY,
                  ticker TEXT UNIQUE,
                  action TEXT,
                  score REAL,
                  reasons TEXT,
                  technical_signals TEXT,
                  created_at TIMESTAMP)''')
    
    # Stock analysis cache
    c.execute('''CREATE TABLE IF NOT EXISTS stock_analysis
                 (id INTEGER PRIMARY KEY,
                  ticker TEXT UNIQUE,
                  data TEXT,
                  created_at TIMESTAMP)''')
    
    # User watchlist
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist
                 (id INTEGER PRIMARY KEY,
                  ticker TEXT UNIQUE,
                  added_at TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def add_recommendation(ticker, action, score, reasons, signals):
    """Add or update recommendation"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''INSERT OR REPLACE INTO recommendations 
                 (ticker, action, score, reasons, technical_signals, created_at)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (ticker, action, score, json.dumps(reasons), json.dumps(signals), datetime.now()))
    
    conn.commit()
    conn.close()

def get_recommendation(ticker):
    """Get recommendation for a stock"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT action, score, reasons, technical_signals FROM recommendations WHERE ticker = ?', (ticker,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "action": row[0],
            "score": row[1],
            "reasons": json.loads(row[2]),
            "signals": json.loads(row[3])
        }
    return None

def get_all_recommendations(limit=10):
    """Get all recommendations"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT ticker, action, score, reasons FROM recommendations ORDER BY score DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def cache_analysis(ticker, data):
    """Cache stock analysis data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''INSERT OR REPLACE INTO stock_analysis
                 (ticker, data, created_at)
                 VALUES (?, ?, ?)''',
              (ticker, json.dumps(data), datetime.now()))
    
    conn.commit()
    conn.close()

def get_cached_analysis(ticker):
    """Get cached analysis"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT data FROM stock_analysis WHERE ticker = ?', (ticker,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return None
