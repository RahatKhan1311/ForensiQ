# routes/auth.py
from flask import Blueprint, app, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import mysql
import MySQLdb.cursors
import jwt
from functools import wraps
from datetime import datetime, timedelta

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

JWT_SECRET = "secretkey123"  # replace with env var in production
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_HOURS = 24

# ---------- SIGNUP ----------
@auth_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not (name and email and password):
            return jsonify({"error": "All fields are required"}), 400

        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Check if email already exists
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            cur.close()
            return jsonify({"error": "Email already registered"}), 400

        cur.execute(
            "INSERT INTO users (name, email, password, created_at) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, datetime.now())
        )
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Signup successful! Please login."}), 200

    except Exception as e:
        return jsonify({"error": "Signup failed", "detail": str(e)}), 500


# ---------- LOGIN ----------
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not (email and password):
            return jsonify({"error": "Email and password required"}), 400

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if not user:
            return jsonify({"error": "User not found"}), 404

        if not check_password_hash(user["password"], password):
            return jsonify({"error": "Incorrect password"}), 401

        # Create JWT token
        payload = {
            "user_id": user["id"],
            "email": user["email"],
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRES_HOURS)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return jsonify({"message": "Login successful", "token": token}), 200

    except Exception as e:
        return jsonify({"error": "Login failed", "detail": str(e)}), 500


# ---------- PROTECTED ROUTE EXAMPLE ----------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # JWT can be sent in Authorization header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(current_user, *args, **kwargs)
    return decorated

# Example protected route
@auth_bp.route("/me", methods=["GET"])
@token_required
def get_me():
    user = getattr(request, "user", None)
    return jsonify({"user": user})

