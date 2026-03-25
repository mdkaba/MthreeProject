from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import get_db_connection

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

        if (hours * 100) % 25 != 0:
            return jsonify({"error": "Hours must be in 0.25 increments"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO tasks (user_id, task_name, task_date, category, hours, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (current_user_id, task_name, task_date, category, hours, description)
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
                "hours": hours,
                "description": description
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500