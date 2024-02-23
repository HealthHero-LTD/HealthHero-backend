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
import pyodbc, struct
from azure import identity


DATABASE_URL = dbm.DATABASE_URL
SECRET_KEY = dbm.SECRET_KEY
CLIENT_ID = os.getenv("CLIENT_ID")
connection_string = os.getenv("AZURE_SQL_CONNECTIONSTRING")

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "super-secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
jwt = JWTManager(app)


@app.post("/login")
def login():
    data = request.get_json()
    try:
        idinfo = id_token.verify_oauth2_token(
            data["id_token"], requests.Request(), CLIENT_ID
        )
        user_id = idinfo["sub"]
        user_email = idinfo["email"]
    except ValueError as e:
        return jsonify({"error": e}), 401

    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_queries.check_login_user_id, (user_id,))
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
                    cursor.execute(
                        sql_queries.insert_login_user_id, (user_id, user_email)
                    )
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


@app.get("/get-user")
@jwt_required()
def get_user():
    try:
        current_user_id = get_jwt_identity()

        with db_cursor() as cursor:
            cursor.execute(
                sql_queries.get_user,
                (current_user_id,),
            )
            row = cursor.fetchone()
            if row:
                last_active_date = row[3].strftime("%Y-%m-%d") if row[3] else None
                user = {
                    "username": row[0],
                    "level": row[1],
                    "xp": row[2],
                    "last_active_date": last_active_date,
                }
                return jsonify(user), 200
            else:
                return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/leaderboard")
def get_leaderboard():
    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_queries.fetch_leaderboard)
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

        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql_queries.check_username,
                    (username,),
                )
                existing_username = cursor.fetchone()

                if existing_username:
                    return jsonify({"error": "username already exists"}), 400

                cursor.execute(
                    sql_queries.update_username,
                    (username, current_user_token_id),
                )
                connection.commit()
        return (
            jsonify({"username": username, "message": "username updated successfully"}),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/update-user")
@jwt_required()
def update_user():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # conver unix timestamp to YYYY-MM-DD
        xp_data = [
            (
                entry["xp"],
                datetime.datetime.fromtimestamp(entry["date"]).strftime("%Y-%m-%d"),
            )
            for entry in data.get("xp_data_array")
            if "xp" in entry and "date" in entry
        ]
        level = data.get("level")
        last_active_date = datetime.datetime.fromtimestamp(
            data.get("last_active_date")
        ).strftime("%Y-%m-%d")
        xp = data.get("xp")

        with db_connection() as connection:
            with connection.cursor() as cursor:
                # Update 'users' table
                cursor.execute(
                    sql_queries.update_users_info,
                    (level, xp, last_active_date, current_user_id),
                )

                # update 'daily' table
                for xp, date in xp_data:
                    cursor.execute(
                        sql_queries.insert_daily_xp,
                        (current_user_id, xp, date, xp),
                    )
        connection.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6969, debug=True)


def db_connection():
    return pg2.connect(DATABASE_URL)


def db_cursor():
    return db_connection().cursor()


def get_conn():
    credential = identity.DefaultAzureCredential(
        exclude_interactive_browser_credential=False
    )
    token_bytes = credential.get_token(
        "https://database.windows.net/.default"
    ).token.encode("UTF-16-LE")
    token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
    SQL_COPT_SS_ACCESS_TOKEN = (
        1256  # This connection option is defined by microsoft in msodbcsql.h
    )
    conn = pyodbc.connect(
        connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct}
    )
    return conn
