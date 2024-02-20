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
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError


DATABASE_URL = dbm.DATABASE_URL
SECRET_KEY = dbm.SECRET_KEY
CLIENT_ID = os.getenv("CLIENT_ID")

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "super-secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
jwt = JWTManager(app)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Disable modification tracking
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User_sqla(db.Model):
    __tablename__ = "users_sqla"

    user_id = db.Column(db.String(256), primary_key=True)
    username = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    xp = db.Column(db.Integer(), nullable=False, default=0)
    level = db.Column(db.Integer(), nullable=False, default=1)
    last_active_date = db.Column(db.Date(), nullable=True)


class Daily_sqla(db.Model):
    __tablename__ = "daily_sqla"

    user_id = db.Column(db.String(256), primary_key=True)
    daily_date = db.Column(db.Date(), nullable=False)
    daily_xp = db.Column(db.Integer(), nullable=False)


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

    user = User_sqla.query.filter_by(user_id=user_id).first()
    access_token = create_access_token(identity=user_id)

    if user:
        return jsonify(
            {
                "access_token": access_token,
                "message": "user already exists",
                "token_id": user_id,
            }
        )
    else:
        try:
            new_user = User_sqla(user_id=user_id, email=user_email)
            db.session.add(new_user)
            db.session.commit()
            return jsonify(
                {
                    "access_token": access_token,
                    "message": "data inserted successfully",
                    "token_id": user_id,
                }
            )
        except IntegrityError as e:
            db.session.rollback()
            print("IntegrityError:", str(e))
            return jsonify({"error": "User already exists"}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500


@app.get("/get-user")
@jwt_required()
def get_user():
    try:
        current_user_id = get_jwt_identity()
        user = User_sqla.query.filter_by(user_id=current_user_id).first()

        if user:
            last_active_date = (
                user.last_active_date.strftime("%Y-%m-%d")
                if user.last_active_date
                else None
            )
            user_data = {
                "username": user.username,
                "level": user.level,
                "xp": user.xp,
                "last_active_date": last_active_date,
            }
            return jsonify(user_data), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/leaderboard")
def get_leaderboard():
    try:
        leaderboard_data = (
            db.session.query(User_sqla.username, User_sqla.level, User_sqla.xp)
            .order_by(User_sqla.level.desc(), User_sqla.xp.desc())
            .all()
        )

        leaderboard_entries = []
        for index, entry in enumerate(leaderboard_data, start=1):
            leaderboard_entry = {
                "id": index,
                "username": entry.username,
                "level": entry.level,
                "score": entry.xp,
            }
            leaderboard_entries.append(leaderboard_entry)
        return jsonify(leaderboard_entries), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/set-username")
@jwt_required()
def set_username():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        new_username = data.get("username")

        existing_user = User_sqla.query.filter_by(username=new_username).first()
        if existing_user:
            return jsonify({"error": "Username already exists"}), 400

        current_user = User_sqla.query.get(current_user_id)
        current_user.username = new_username
        db.session.commit()

        return (
            jsonify(
                {"username": new_username, "message": "Username updated successfully"}
            ),
            200,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.post("/update-user")
@jwt_required()
def update_user():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # Convert Unix timestamp to YYYY-MM-DD
        xp_data = [
            {
                "xp": entry["xp"],
                "date": datetime.datetime.fromtimestamp(entry["date"]).strftime(
                    "%Y-%m-%d"
                ),
            }
            for entry in data.get("xp_data_array")
            if "xp" in entry and "date" in entry
        ]
        level = data.get("level")
        last_active_date = datetime.datetime.fromtimestamp(
            data.get("last_active_date")
        ).strftime("%Y-%m-%d")
        xp = data.get("xp")

        # Update 'users_sqla' table
        user = User_sqla.query.get(current_user_id)
        if user:
            user.level = level
            user.xp = xp
            user.last_active_date = last_active_date
            db.session.commit()

            # Update 'daily_sqla' table
            for entry in xp_data:
                daily_entry = Daily_sqla.query.filter_by(
                    user_id=current_user_id, daily_date=entry["date"]
                ).first()

                if daily_entry:
                    daily_entry.daily_xp = entry["xp"]
                else:
                    new_daily_entry = Daily_sqla(
                        user_id=current_user_id,
                        daily_date=entry["date"],
                        daily_xp=entry["xp"],
                    )
                    db.session.add(new_daily_entry)

            db.session.commit()

            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": "User not found"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6969, debug=True)
