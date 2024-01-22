import os
import psycopg2 as pg2
import sql_queries
import db_management as dbm
from flask import Flask, request, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

DATABASE_URL = dbm.DATABASE_URL
SECRET_KEY = dbm.SECRET_KEY
CLIENT_ID = os.getenv("CLIENT_ID")
app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "super-secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 7 * 24 * 60 * 60
jwt = JWTManager(app)


@app.route("/")
def hello():
    return "hello"


@app.get("/user-profile")
def index_get():
    return "GET request reveived"


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
        print(googleid)
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
                            }
                        )
                    else:
                        cursor.execute(
                            sql_queries.inser_googleid_users, (googleid, 200)
                        )
                        connection.commit()
            return jsonify(
                {
                    "access_token": access_token,
                    "message": "data inserted successfully",
                    "googleID": googleid,
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)})
    except ValueError:
        print("invalid token")
        return jsonify({"error": ValueError})


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
        return jsonify("error": str(e)), 500


@app.get("/steps")
@jwt_required()
def steps():
    return "hey"


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
        return jsonify(message="error updating steps"), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6969, debug=True)
