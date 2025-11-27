import sqlite3
import os, sys

def get_db_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, "tinkoff_analyzer.db")

DB_FILE = get_db_path()


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instruments_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument_uid TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            ticker TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument_uid TEXT NOT NULL,
            instrument_name TEXT,
            price REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT DEFAULT 'STREAM'
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_instruments_uid ON instruments_cache(instrument_uid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_uid ON price_history(instrument_uid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history(timestamp)")
    
    conn.commit()
    conn.close()



def get_all_accounts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, token FROM accounts")
    rows = cursor.fetchall()
    conn.close()
    return {row['name']: row['token'] for row in rows}


def get_account_token(account_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT token FROM accounts WHERE name = ?", (account_name,))
    row = cursor.fetchone()
    conn.close()
    return row['token'] if row else None


def save_account(account_name, token):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO accounts (name, token, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                token = excluded.token,
                updated_at = CURRENT_TIMESTAMP
        """, (account_name, token))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_account(account_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM accounts WHERE name = ?", (account_name,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_cached_instrument(instrument_uid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM instruments_cache WHERE instrument_uid = ?", (instrument_uid,))
    row = cursor.fetchone()
    conn.close()
    return row['name'] if row else None


def get_cached_ticker(instrument_uid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ticker FROM instruments_cache WHERE instrument_uid = ?", (instrument_uid,))
    row = cursor.fetchone()
    conn.close()
    return row['ticker'] if row and row['ticker'] else None


def cache_instrument(instrument_uid, name, ticker=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO instruments_cache (instrument_uid, name, ticker, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(instrument_uid) DO UPDATE SET
                name = excluded.name,
                ticker = excluded.ticker,
                updated_at = CURRENT_TIMESTAMP
        """, (instrument_uid, name, ticker))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()


def get_all_cached_instruments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT instrument_uid, name, ticker FROM instruments_cache")
    rows = cursor.fetchall()
    conn.close()
    return {row['instrument_uid']: row['name'] for row in rows}


def get_cached_instrument_ticker():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ticker FROM instruments_cache')
    rows = cursor.fetchall()
    conn.close()
    return [row['ticker'] for row in rows]


def save_price(instrument_uid, price, instrument_name = None,
               source = 'STREAM'):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO price_history (instrument_uid, instrument_name, price, source)
            VALUES (?, ?, ?, ?)
        """, (instrument_uid, instrument_name, price, source))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    finally:
        conn.close()
        
def clear_accounts():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM accounts")
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()


init_database()

