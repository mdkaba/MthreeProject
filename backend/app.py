from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from db import get_db_connection
from routes.auth_routes import auth_bp
from routes.task_routes import task_bp
from routes.lookup_routes import lookup_bp
from routes.admin_routes import admin_bp

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY

CORS(app)
jwt = JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(task_bp)
app.register_blueprint(lookup_bp)
app.register_blueprint(admin_bp)

@app.route("/")
def home():
    return {"message": "Backend is running"}


@app.route("/test-db")
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()

        cursor.close()
        conn.close()

        return {"message": f"Connected to database: {db_name[0]}"}
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(debug=True)