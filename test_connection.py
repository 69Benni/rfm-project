from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    print("✅ Connexion MySQL réussie!")
    conn.close()
except Exception as e:
    print(f"❌ Erreur: {e}")