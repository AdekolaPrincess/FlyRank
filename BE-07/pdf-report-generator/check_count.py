import sqlite3

conn = sqlite3.connect("report.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM books")
result = cursor.fetchone()

print(f"Row count: {result[0]}")

conn.close()