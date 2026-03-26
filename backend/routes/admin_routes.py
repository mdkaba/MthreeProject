from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/api/admin/users", methods=["GET"])
@jwt_required()
def get_all_users():
    try:
        current_user_id = get_jwt_identity()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Step 1: check if current user is admin
        cursor.execute(
            """
            SELECT role
            FROM users
            WHERE id = %s
            """,
            (current_user_id,)
        )
        current_user = cursor.fetchone()

        if not current_user:
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404

        if current_user["role"] != "admin":
            cursor.close()
            conn.close()
            return jsonify({"error": "Access denied. Admins only."}), 403

        # Step 2: fetch all users with region and team
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
            ORDER BY u.id ASC
            """
        )
        users = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"users": users}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/api/admin/users/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user_by_admin(user_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        role = data.get("role")
        region_id = data.get("region_id")
        team_id = data.get("team_id")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Step 1: check if current user is admin
        cursor.execute(
            """
            SELECT role
            FROM users
            WHERE id = %s
            """,
            (current_user_id,)
        )
        current_user = cursor.fetchone()

        if not current_user:
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404

        if current_user["role"] != "admin":
            cursor.close()
            conn.close()
            return jsonify({"error": "Access denied. Admins only."}), 403

        # Step 2: check if target user exists
        cursor.execute(
            """
            SELECT id, username, email, role, region_id, team_id
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )
        target_user = cursor.fetchone()

        if not target_user:
            cursor.close()
            conn.close()
            return jsonify({"error": "Target user not found"}), 404

        # Step 3: validate role if provided
        allowed_roles = ["user", "admin"]
        if role is not None and role not in allowed_roles:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid role. Allowed values are 'user' and 'admin'."}), 400

        # Step 4: validate region_id if provided
        if region_id is not None:
            cursor.execute(
                """
                SELECT id
                FROM regions
                WHERE id = %s
                """,
                (region_id,)
            )
            region = cursor.fetchone()

            if not region:
                cursor.close()
                conn.close()
                return jsonify({"error": "Invalid region_id"}), 400

        # Step 5: validate team_id if provided
        if team_id is not None:
            cursor.execute(
                """
                SELECT id
                FROM teams
                WHERE id = %s
                """,
                (team_id,)
            )
            team = cursor.fetchone()

            if not team:
                cursor.close()
                conn.close()
                return jsonify({"error": "Invalid team_id"}), 400

        # Step 6: preserve old values if field not provided
        updated_role = role if role is not None else target_user["role"]
        updated_region_id = region_id if region_id is not None else target_user["region_id"]
        updated_team_id = team_id if team_id is not None else target_user["team_id"]

        # Step 7: update the target user
        cursor.execute(
            """
            UPDATE users
            SET role = %s,
                region_id = %s,
                team_id = %s
            WHERE id = %s
            """,
            (updated_role, updated_region_id, updated_team_id, user_id)
        )
        conn.commit()

        # Step 8: fetch updated user with readable region/team names
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
            (user_id,)
        )
        updated_user = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({
            "message": "User updated successfully",
            "user": updated_user
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/api/admin/tasks", methods=["GET"])
@jwt_required()
def get_all_tasks_by_admin():
    try:
        current_user_id = get_jwt_identity()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Step 1: check if current user is admin
        cursor.execute(
            """
            SELECT role
            FROM users
            WHERE id = %s
            """,
            (current_user_id,)
        )
        current_user = cursor.fetchone()

        if not current_user:
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404

        if current_user["role"] != "admin":
            cursor.close()
            conn.close()
            return jsonify({"error": "Access denied. Admins only."}), 403

        # Step 2: fetch all tasks with user, region, and team info
        cursor.execute(
            """
            SELECT
                t.id,
                t.user_id,
                t.task_name,
                t.task_date,
                t.category,
                t.hours,
                t.description,
                t.created_at,
                u.username,
                u.email,
                u.role,
                r.name AS region,
                tm.name AS team
            FROM tasks t
            INNER JOIN users u ON t.user_id = u.id
            LEFT JOIN regions r ON u.region_id = r.id
            LEFT JOIN teams tm ON u.team_id = tm.id
            ORDER BY t.task_date DESC, t.id DESC
            """
        )
        tasks = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"tasks": tasks}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500