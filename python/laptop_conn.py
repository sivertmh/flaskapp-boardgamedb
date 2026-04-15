import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Db-kobling.
def ltdb_connect():
    # Kobler til laptop-db (ltdb) med info fra Environment-fil.
    return mysql.connector.connect(
        database=os.environ.get("DB_NAME"),
        host=os.environ.get("LTDB_HOST"),
        user=os.environ.get("LTDB_USER"),
        password=os.environ.get("LTDB_PASSWORD"),
    )
