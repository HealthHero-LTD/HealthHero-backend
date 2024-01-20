import psycopg2
import jwt
import sql_queries
import os

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}" f"@localhost:5432/{DB_NAME}"
SECRET_KEY = "test-token"


def generate_token(username, secret_key):
    payload = {"username": username}
    return jwt.encode(payload, secret_key, algorithm="HS256")


def save_token_to_database(username, token, database_url):
    print(f"Saving token {token} for user {username}")
    with psycopg2.connect(database_url) as dbConnection:
        with dbConnection.cursor() as cursor:
            cursor.execute(sql_queries.update_token_query, (token, username))
            dbConnection.commit()
