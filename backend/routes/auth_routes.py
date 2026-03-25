from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/register", methods=["POST"])
def register():
    try:
        data = request.get_json()

        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not username or not email or not password:
            return jsonify({"error": "Username, email, and password are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE email = %s OR username = %s",
            (email, username)
        )
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({"error": "User already exists"}), 409

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (username, email, password_hash)
        )
        conn.commit()

        new_user_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify({
            "message": "User registered successfully",
            "user": {
                "id": new_user_id,
                "username": username,
                "email": email
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, username, email, password_hash, role
            FROM users
            WHERE email = %s
            """,
            (email,)
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        if not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid email or password"}), 401

        access_token = create_access_token(
            identity=str(user["id"]),
            additional_claims={
                "username": user["username"],
                "role": user["role"]
            }
        )

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"]
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route("/api/me", methods=["GET"])
@jwt_required()
def get_current_user():
    try:
        current_user_id = get_jwt_identity()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, username, email, role, created_at
            FROM users
            WHERE id = %s
            """,
            (current_user_id,)
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"user": user}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500