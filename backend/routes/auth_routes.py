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

        region_id = data.get("region_id")
        team_id = data.get("team_id")

        # Basic validation
        if not username or not email or not password:
            return jsonify({"error": "Username, email, and password are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if user already exists
        cursor.execute(
            "SELECT id FROM users WHERE email = %s OR username = %s",
            (email, username)
        )
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({"error": "User already exists"}), 409

        # Validate region_id (if provided)
        if region_id:
            cursor.execute("SELECT id FROM regions WHERE id = %s", (region_id,))
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({"error": "Invalid region_id"}), 400

        # Validate team_id (if provided)
        if team_id:
            cursor.execute("SELECT id FROM teams WHERE id = %s", (team_id,))
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({"error": "Invalid team_id"}), 400

        # Hash password
        password_hash = generate_password_hash(password)

        # Insert user WITH region + team
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role, region_id, team_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (username, email, password_hash, "user", region_id, team_id)
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
                "email": email,
                "region_id": region_id,
                "team_id": team_id
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
            SELECT 
                u.id,
                u.username,
                u.email,
                u.role,
                u.created_at,
                u.region_id,
                u.team_id,
                r.name AS region,
                t.name AS team
            FROM users u
            LEFT JOIN regions r ON u.region_id = r.id
            LEFT JOIN teams t ON u.team_id = t.id
            WHERE u.id = %s
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