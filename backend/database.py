import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "data/game.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            start_date TEXT NOT NULL,
            current_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            duration TEXT NOT NULL,
            cash REAL NOT NULL DEFAULT 1000000,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT,
            amount INTEGER NOT NULL,
            cost_price REAL NOT NULL,
            buy_date TEXT NOT NULL,
            FOREIGN KEY (game_id) REFERENCES games(id)
        );

        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            price REAL NOT NULL,
            amount INTEGER NOT NULL,
            trade_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_id) REFERENCES games(id)
        );

        CREATE TABLE IF NOT EXISTS rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            user_name TEXT,
            start_date TEXT NOT NULL,
            duration TEXT NOT NULL,
            initial_cash REAL NOT NULL,
            final_assets REAL NOT NULL,
            profit_rate REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_id) REFERENCES games(id)
        );
    """)
    conn.commit()
    conn.close()
