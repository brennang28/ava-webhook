import sqlite3
db_path = "jobs.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT * FROM jobs WHERE company LIKE '%AMC%';")
amc = cursor.fetchall()
print(f"AMC entries: {len(amc)}")
for a in amc:
    print(a)
conn.close()
