import sqlite3
import pandas as pd

def query_db():
    try:
        conn = sqlite3.connect('jobs.db')
        query = "SELECT title, company FROM jobs WHERE title LIKE '%Intern%' OR title LIKE '%Contract%' OR title LIKE '%Temp%';"
        df = pd.read_sql_query(query, conn)
        print(f"Found {len(df)} roles matching Intern/Contract/Temp:")
        print(df)
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    query_db()
