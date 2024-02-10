import psycopg2 as pg2
import jwt
import sql_queries
import os

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}" f"@localhost:5432/{DB_NAME}"
SECRET_KEY = "test-token"
