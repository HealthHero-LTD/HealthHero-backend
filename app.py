import os
import psycopg2 as pg2
import sql_queries
import db_management as dbm
from flask import Flask, request, jsonify
from datetime import timedelta
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager


DATABASE_URL = dbm.DATABASE_URL
SECRET_KEY = dbm.SECRET_KEY
CLIENT_ID = os.getenv("CLIENT_ID")
app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "super-secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
jwt = JWTManager(app)


@app.post("/login")
def login():
    data = request.get_json()
    print(f"received data: {data}")
    print(data.get("idToken"))
    try:
        idinfo = id_token.verify_oauth2_token(
            data["idToken"], requests.Request(), CLIENT_ID
        )
        googleid = idinfo["sub"]
        expiration_time = idinfo["exp"]
        print(googleid)
        print(expiration_time)
    except ValueError as e:
        return jsonify({"error": e}), 401

    try:
        with pg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT googleid FROM users WHERE googleid=%s", (googleid,)
                )
                googleid_exist = cursor.fetchone()
                access_token = create_access_token(identity=googleid)

                if googleid_exist:
                    return jsonify(
                        {
                            "access_token": access_token,
                            "message": "user already exists",
                            "GoogleID": googleid,
                            "expiration_time": expiration_time,
                        }
                    )
                else:
                    cursor.execute(sql_queries.insert_googleid_users, (googleid, 200))
                    connection.commit()
        return jsonify(
            {
                "access_token": access_token,
                "message": "data inserted successfully",
                "googleID": googleid,
                "expiration_time": expiration_time,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)})


@app.get("/update_steps")
@jwt_required()
def update_steps():
    try:
        current_user = get_jwt_identity()
        with pg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                new_steps = request.json.get("steps")
                update_query = "UPDATE users SET steps = %s WHERE googleid=%s"
                cursor.execute(update_query, (new_steps, current_user))
                connection.commit()

                return jsonify(message="steps updated"), new_steps

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/leaderboard")
def get_leaderboard():
    print("breakpoint1")
    try:
        with pg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                query = """
                SELECT username, LEVEL, steps
                FROM USERS 
                ORDER BY level DESC, steps DESC;
                """
                cursor.execute(query)
                leaderboard_data = cursor.fetchall()

        leaderboard_entries = []
        id = 1
        for row in leaderboard_data:
            leaderboard_entry = {
                "id": id,
                "username": row[0],
                "level": row[1],
                "score": row[2],
            }
            leaderboard_entries.append(leaderboard_entry)
            id += 1
        return jsonify(leaderboard_entries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6969, debug=True)
