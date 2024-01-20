import psycopg2
import sql_queries
import db_management as dbm
from flask import Flask, request, jsonify

DATABASE_URL = dbm.DATABASE_URL
SECRET_KEY = dbm.SECRET_KEY

app = Flask(__name__)


@app.route("/")
def hello():
    return "hello"


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
                cursor.execute(
                    sql_queries.insert_user_query,
                    (data["username"], data["google_email_address"], data["steps"]),
                )
                dbConnection.commit()
                print("table 'user' created successfully")
                token = dbm.generate_token(data["username"], SECRET_KEY)
                dbm.save_token_to_database(data["username"], token, DATABASE_URL)
            return jsonify({"message": "data transferred!", "token": token})
    except Exception as e:
        return jsonify({"error": str(e)})


# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=6969, debug=True)
