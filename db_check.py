import sqlite3

conn = sqlite3.connect('sarathi_feed.db')
cursor = conn.cursor()

print("Connected to sarathi_feed.db")

# Show tables in the database
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

# Optional: show columns in feed_entries
if ('feed_entries',) in tables:
    cursor.execute("PRAGMA table_info(feed_entries);")
    columns = [col[1] for col in cursor.fetchall()]
    print("Columns in feed_entries:", columns)

# Interactive SQL prompt
print("\nType your SQL query below (type 'exit' to quit):")
while True:
    query = input("SQL> ")
    if query.lower() in ('exit', 'quit'):
        break
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        for row in results:
            print(row)
    except sqlite3.Error as e:
        print("Error:", e)

conn.close()
print("Connection closed.")
