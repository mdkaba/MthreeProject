from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection
from utils.time_utils import round_to_quarter_hour

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/api/tasks", methods=["POST"])
@jwt_required()
def create_task():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        task_name = data.get("task_name", "").strip()
        task_date = data.get("task_date", "").strip()
        category = data.get("category", "").strip()
        if not category:
            category = "Uncategorized"
        description = data.get("description", "").strip()
        hours = data.get("hours")

        if not task_name or not task_date or hours is None:
            return jsonify({
                "error": "task_name, task_date, and hours are required"
            }), 400

        try:
            hours = float(hours)
        except (TypeError, ValueError):
            return jsonify({"error": "Hours must be a valid number"}), 400

        if hours <= 0:
            return jsonify({"error": "Hours must be greater than 0"}), 400

        original_hours = hours
        rounded_hours = round_to_quarter_hour(hours)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO tasks (user_id, task_name, task_date, category, hours, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                current_user_id,
                task_name,
                task_date,
                category,
                rounded_hours,
                description
            )
        )
        conn.commit()

        new_task_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify({
            "message": "Task created successfully",
            "task": {
                "id": new_task_id,
                "user_id": current_user_id,
                "task_name": task_name,
                "task_date": task_date,
                "category": category,
                "hours_entered": original_hours,
                "hours_stored": rounded_hours,
                "description": description
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@task_bp.route("/api/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    try:
        current_user_id = get_jwt_identity()
        month = request.args.get("month", "").strip()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if month:
            cursor.execute(
                """
                SELECT id, user_id, task_name, task_date, category, hours, description, created_at
                FROM tasks
                WHERE user_id = %s
                  AND DATE_FORMAT(task_date, '%Y-%m') = %s
                ORDER BY task_date DESC, id DESC
                """,
                (current_user_id, month)
            )
        else:
            cursor.execute(
                """
                SELECT id, user_id, task_name, task_date, category, hours, description, created_at
                FROM tasks
                WHERE user_id = %s
                ORDER BY task_date DESC, id DESC
                """,
                (current_user_id,)
            )

        tasks = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "month": month if month else None,
            "tasks": tasks
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@task_bp.route("/api/tasks/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        task_name = data.get("task_name", "").strip()
        task_date = data.get("task_date", "").strip()
        category = data.get("category", "").strip()
        if not category:
            category = "Uncategorized"
        description = data.get("description", "").strip()
        hours = data.get("hours")

        if not task_name or not task_date or hours is None:
            return jsonify({
                "error": "task_name, task_date, and hours are required"
            }), 400

        try:
            hours = float(hours)
        except (TypeError, ValueError):
            return jsonify({"error": "Hours must be a valid number"}), 400

        if hours <= 0:
            return jsonify({"error": "Hours must be greater than 0"}), 400

        original_hours = hours
        rounded_hours = round_to_quarter_hour(hours)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, user_id
            FROM tasks
            WHERE id = %s AND user_id = %s
            """,
            (task_id, current_user_id)
        )
        existing_task = cursor.fetchone()

        if not existing_task:
            cursor.close()
            conn.close()
            return jsonify({"error": "Task not found or unauthorized"}), 404

        cursor.execute(
            """
            UPDATE tasks
            SET task_name = %s,
                task_date = %s,
                category = %s,
                hours = %s,
                description = %s
            WHERE id = %s AND user_id = %s
            """,
            (
                task_name,
                task_date,
                category,
                rounded_hours,
                description,
                task_id,
                current_user_id
            )
        )
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "message": "Task updated successfully",
            "task": {
                "id": task_id,
                "user_id": current_user_id,
                "task_name": task_name,
                "task_date": task_date,
                "category": category,
                "hours_entered": original_hours,
                "hours_stored": rounded_hours,
                "description": description
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@task_bp.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    try:
        current_user_id = get_jwt_identity()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, user_id, task_name
            FROM tasks
            WHERE id = %s AND user_id = %s
            """,
            (task_id, current_user_id)
        )
        existing_task = cursor.fetchone()

        if not existing_task:
            cursor.close()
            conn.close()
            return jsonify({"error": "Task not found or unauthorized"}), 404

        cursor.execute(
            """
            DELETE FROM tasks
            WHERE id = %s AND user_id = %s
            """,
            (task_id, current_user_id)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "message": "Task deleted successfully",
            "deleted_task": {
                "id": existing_task["id"],
                "task_name": existing_task["task_name"]
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@task_bp.route("/api/tasks/summary", methods=["GET"])
@jwt_required()
def get_task_summary():
    try:
        current_user_id = get_jwt_identity()
        month = request.args.get("month", "").strip()

        if not month:
            return jsonify({"error": "Month is required in the format YYYY-MM"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT 
                category AS activity,
                CAST(SUM(hours) AS DECIMAL(10,2)) AS total_hours,
                COUNT(*) AS count
            FROM tasks
            WHERE user_id = %s
              AND DATE_FORMAT(task_date, '%Y-%m') = %s
            GROUP BY COALESCE(NULLIF(category, ''), 'Uncategorized')
            ORDER BY total_hours DESC, activity ASC
            """,
            (current_user_id, month)
        )
        activities = cursor.fetchall()

        cursor.execute(
            """
            SELECT 
                CAST(COALESCE(SUM(hours), 0) AS DECIMAL(10,2)) AS total_hours,
                COUNT(*) AS total_count
            FROM tasks
            WHERE user_id = %s
              AND DATE_FORMAT(task_date, '%Y-%m') = %s
            """,
            (current_user_id, month)
        )
        grand_total = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({
            "month": month,
            "activities": activities,
            "grand_total": grand_total
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500