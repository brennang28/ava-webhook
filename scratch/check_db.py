import sqlite3
import os

db_path = "jobs.db"
if not os.path.exists(db_path):
    print(f"{db_path} does not exist")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    
    if tables:
        # Check count
        cursor.execute("SELECT COUNT(*) FROM jobs;")
        count = cursor.fetchone()[0]
        print(f"Total jobs: {count}")
        
        # Check for duplicates by company and title
        cursor.execute("SELECT company, title, COUNT(*) as count FROM jobs GROUP BY company, title HAVING count > 1;")
        dupes = cursor.fetchall()
        print(f"Duplicates by company/title: {len(dupes)}")
        for d in dupes:
            print(d)
            
        # Check for duplicates by job_id
        cursor.execute("SELECT job_id, COUNT(*) as count FROM jobs GROUP BY job_id HAVING count > 1;")
        id_dupes = cursor.fetchall()
        print(f"Duplicates by job_id: {len(id_dupes)}")
        
        # Look for AMC Global Media
        cursor.execute("SELECT * FROM jobs WHERE company LIKE '%AMC Global Media%';")
        amc = cursor.fetchall()
        print(f"AMC Global Media entries: {len(amc)}")
        for a in amc:
            print(a)
            
    conn.close()
