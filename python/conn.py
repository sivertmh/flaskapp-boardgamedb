import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Db-kobling.
def db_connect():
    # Kobler til db med info fra Environment-fil.
    return mysql.connector.connect(
        database=os.environ.get("DB_NAME"),
        port=os.environ.get("DB_PORT"),
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
    )
    