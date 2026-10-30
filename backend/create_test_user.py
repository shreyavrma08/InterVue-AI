import sqlite3

# Connect to your SQLite database file
conn = sqlite3.connect("sql_app.db")  # Replace with your .db file name if different
cursor = conn.cursor()

# Insert test user directly
cursor.execute("""
    INSERT OR IGNORE INTO users (email, hashed_password)
    VALUES ('test@example.com', 'password123')
""")

conn.commit()
conn.close()
print("Test user created successfully!")