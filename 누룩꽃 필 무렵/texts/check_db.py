import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv(r"c:\dev\KLIEN\murdex\murdex-api\.env")

conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    port=int(os.getenv("MYSQL_PORT")),
    database=os.getenv("MYSQL_DATABASE"),
    user=os.getenv("MYSQL_USERNAME"),
    password=os.getenv("MYSQL_PASSWORD")
)

cursor = conn.cursor()
cursor.execute("SHOW TABLES LIKE '%clue%'")
print("Tables:", cursor.fetchall())

cursor.execute("DESCRIBE clues")
columns = cursor.fetchall()
for col in columns:
    print(col)

cursor.close()
conn.close()
