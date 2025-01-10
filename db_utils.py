import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os 
import pandas as pd
from datetime import datetime, timedelta
from constants import STATUS_COMPLETED, STATUS_IN_PROCESS, EXPIRED_ANNOTATION_THRESHOLD, DB_PATH

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")
def get_sqlalchemy_engine():
    """Create and return an SQLAlchemy engine for PostgreSQL."""
    db_url = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?options=-csearch_path=public"
    return create_engine(db_url)

def get_db_connection():
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )
    return connection

def fetch_unannotated_doc():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Remove expired "in process" annotations
        cursor.execute("""
            DELETE FROM public.annotations 
            WHERE status = %s AND time::timestamp < NOW() - INTERVAL %s
        """, (STATUS_IN_PROCESS, f'{EXPIRED_ANNOTATION_THRESHOLD} minutes'))
        
        # Fetch unannotated document
        cursor.execute("""
            SELECT d.doc_id, d.drugs
            FROM public.documents d
            LEFT JOIN public.annotations a ON d.doc_id = a.doc_id
            WHERE a.doc_id IS NULL
            LIMIT 1
        """)
        doc = cursor.fetchone()
        
        if doc:
            # Mark document as "in process"
            cursor.execute("""
                INSERT INTO public.annotations (doc_id, status, time)
                VALUES (%s, %s, %s)
            """, (doc[0], STATUS_IN_PROCESS, datetime.now().isoformat()))
            conn.commit()
        
        return doc

def fetch_structured_drugs(doc_id):
    with get_db_connection() as conn:
        return pd.read_sql_query("SELECT * FROM public.drugs_structured WHERE doc_id = %s", conn, params=(doc_id,))

def save_annotation(doc_id, username, df):
    engine = get_sqlalchemy_engine()
    with engine.connect() as connection:
        # Save to `drugs_structured_check`
        df.to_sql('drugs_structured_check', con=engine, schema='public', if_exists='append', index=False)

        with get_db_connection() as conn:        
        # Update annotations
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE public.annotations
                SET status = %s, username = %s, save_time = %s
                WHERE doc_id = %s AND status = %s
            """, (STATUS_COMPLETED, username, datetime.now().isoformat(), doc_id, STATUS_IN_PROCESS))
            conn.commit()

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.annotations (
                id SERIAL PRIMARY KEY,
                doc_id INTEGER,
                username TEXT,
                status TEXT,
                time TEXT,
                save_time TEXT,
                CONSTRAINT fk_documents FOREIGN KEY (doc_id) REFERENCES documents(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.drugs_structured_check (
                id SERIAL PRIMARY KEY,
                doc_id INTEGER,
                name TEXT,
                form TEXT,
                dosage TEXT,
                concentration TEXT,
                frequency TEXT,
                duration TEXT,
                route TEXT,
                CONSTRAINT fk_documents FOREIGN KEY (doc_id) REFERENCES documents(id)
            )
        """)
        conn.commit()

def check_db_structure():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = cursor.fetchall()
        print("Existing tables:", tables)
        
        for table in tables:
            cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                """, (table[0],))
            columns = cursor.fetchall()
            print(f"\nColumns in {table[0]}:")
            for column in columns:
                print(column)

if __name__ == "__main__":
    check_db_structure()