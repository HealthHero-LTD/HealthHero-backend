import os
import psycopg2 as pg2
import sql_queries
import db_management as dbm
from flask import Flask, request, jsonify
from datetime import timedelta
import datetime
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
    try:
        idinfo = id_token.verify_oauth2_token(
            data["idToken"], requests.Request(), CLIENT_ID
        )
        user_id = idinfo["sub"]
        user_email = idinfo["email"]
        print(user_id)
        print(user_email)

    except ValueError as e:
        return jsonify({"error": e}), 401

    try:
        with pg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users WHERE user_id=%s", (user_id,))
                user_id_exist = cursor.fetchone()
                access_token = create_access_token(
                    identity=user_id
                )  # Health Hero token

                if user_id_exist:
                    return jsonify(
                        {
                            "access_token": access_token,
                            "message": "user already exists",
                            "token_id": user_id,
                        }
                    )
                else:
                    cursor.execute(sql_queries.insert_user_id, (user_id, user_email))
                    connection.commit()
        return jsonify(
            {
                "access_token": access_token,
                "message": "data inserted successfully",
                "token_id": user_id,
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
    try:
        with pg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                query = """
                SELECT username, level, steps
                FROM leaderboard 
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


@app.post("/set-username")
@jwt_required()
def set_username():
    try:
        current_user_token_id = get_jwt_identity()
        data = request.get_json()
        username = data.get("username")

        with pg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT username FROM users WHERE username = %s LIMIT 1",
                    (username,),
                )
                existing_username = cursor.fetchone()

                if existing_username:
                    return jsonify({"error": "username already exists"}), 400

                cursor.execute(
                    "UPDATE users SET username = %s WHERE user_id = %s",
                    (username, current_user_token_id),
                )
                connection.commit()
        return jsonify({"message": "username updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/update-xp")
@jwt_required()
def update_XP():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # conver unix timestamp to YYYY-MM-DD
        xp_data = [
            (
                entry["xp"],
                datetime.datetime.fromtimestamp(entry["date"]).strftime("%Y-%m-%d"),
            )
            for entry in data
            if "xp" in entry and "date" in entry
        ]

        with pg2.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                # update 'users' table
                total_xp = sum(xp for xp, _ in xp_data)
                cursor.execute(
                    """
                    UPDATE users
                    SET xp = %s
                    WHERE user_id = %s
                    """,
                    (total_xp, current_user_id),
                )

                # update 'daily' table
                for xp, date in xp_data:
                    cursor.execute(
                        """
                        INSERT INTO daily (user_id, daily_xp, daily_date)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id, daily_date)
                        DO UPDATE SET daily_xp = %s
                        """,
                        (current_user_id, xp, date, xp),
                    )

        connection.commit()

        return jsonify({"message": "XP updated successfully."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6969, debug=True)
