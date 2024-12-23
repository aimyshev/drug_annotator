import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from constants import STATUS_COMPLETED, STATUS_IN_PROCESS, EXPIRED_ANNOTATION_THRESHOLD, DB_PATH

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def fetch_unannotated_doc():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Remove expired "in process" annotations
        cursor.execute("""
            DELETE FROM annotations 
            WHERE status = ? AND datetime(time) < datetime('now', ?)
        """, (STATUS_IN_PROCESS, f'-{EXPIRED_ANNOTATION_THRESHOLD} minutes'))
        
        # Fetch unannotated document
        cursor.execute("""
            SELECT d.doc_id, d.drugs
            FROM documents d
            LEFT JOIN annotations a ON d.doc_id = a.doc_id
            WHERE a.doc_id IS NULL
            LIMIT 1
        """)
        doc = cursor.fetchone()
        
        if doc:
            # Mark document as "in process"
            cursor.execute("""
                INSERT INTO annotations (doc_id, status, time)
                VALUES (?, ?, ?)
            """, (doc[0], STATUS_IN_PROCESS, datetime.now().isoformat()))
            conn.commit()
        
        return doc

def fetch_structured_drugs(doc_id):
    with get_db_connection() as conn:
        return pd.read_sql_query("SELECT * FROM drugs_structured WHERE doc_id = ?", conn, params=(doc_id,))

def save_annotation(doc_id, username, df):
    with get_db_connection() as conn:
        # Save to drugs_structured_check
        df.to_sql('drugs_structured_check', conn, if_exists='append', index=False)
        
        # Update annotations
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE annotations
            SET status = ?, username = ?, save_time = ?
            WHERE doc_id = ? AND status = ?
        """, (STATUS_COMPLETED, username, datetime.now().isoformat(), doc_id, STATUS_IN_PROCESS))
        conn.commit()

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER,
                username TEXT,
                status TEXT,
                time TEXT,
                save_time TEXT,
                FOREIGN KEY (doc_id) REFERENCES documents(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drugs_structured_check (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER,
                name TEXT,
                form TEXT,
                dosage TEXT,
                concentration TEXT,
                frequency TEXT,
                duration TEXT,
                route TEXT,
                FOREIGN KEY (doc_id) REFERENCES documents(id)
            )
        """)
        conn.commit()

def check_db_structure():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Existing tables:", tables)
        
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            print(f"\nColumns in {table[0]}:")
            for column in columns:
                print(column)

if __name__ == "__main__":
    check_db_structure()