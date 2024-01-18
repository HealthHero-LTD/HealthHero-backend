import os
import psycopg2
import jwt
from flask import Flask, request, jsonify

# db configs
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@localhost:5432/{DB_NAME}"
)

SECRET_KEY = "test-token"
# query blocks
create_userTable_query = """
CREATE TABLE IF NOT EXISTS "user-profile"(
    username VARCHAR(50) PRIMARY KEY,
    google_email_address VARCHAR(50) UNIQUE,
    steps INTEGER
);

ALTER TABLE "user-profile"
ADD COLUMN token VARCHAR(256);
"""

app = Flask(__name__)

############
def generate_token(username):
    payload = {'username': username}
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def save_token_to_database(username, token):
    with psycopg2.connect(DATABASE_URL) as dbConnection:
        with dbConnection.cursor() as cursor:
            update_query = """
            UPDATE "user-profile"
            SET token = %s
            WHERE username = %s;
            """
            cursor.execute(update_query, (username, token))
            dbConnection.commit()
#############

@app.route('/')
def hello():
    return('hello')

@app.get("/user-profile")
def index_get():
    return "GET request reveived"

@app.post("/user-profile")
def index_post():
    data = request.get_json()
    print(f"received data: {data}")
    
    try:
        with psycopg2.connect(DATABASE_URL) as dbConnection:
            with dbConnection.cursor() as cursor:
                cursor.execute(create_userTable_query)
                
                insert_query = """
                INSERT INTO "user-profile" (username, google_email_address, steps)
                VALUES (%s, %s, %s);
                """
                cursor.execute(insert_query, (data['username'], 
                                              data['google_email_address'], 
                                              data['steps'])
                               )
                dbConnection.commit()
                print("table 'user' created successfully")
                token = generate_token(data['username'])
                save_token_to_database(data['username'], token)
            return jsonify({'message': 'data transferred!', 'token': token})
    except Exception as e:
        return jsonify({'error': str(e)})

    
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=6969, debug=True)