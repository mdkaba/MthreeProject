from flask import Blueprint, jsonify
from db import get_db_connection

lookup_bp = Blueprint("lookup", __name__)


@lookup_bp.route("/api/regions", methods=["GET"])
def get_regions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name
            FROM regions
            ORDER BY name ASC
            """
        )
        regions = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"regions": regions}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@lookup_bp.route("/api/teams", methods=["GET"])
def get_teams():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name
            FROM teams
            ORDER BY name ASC
            """
        )
        teams = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"teams": teams}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500