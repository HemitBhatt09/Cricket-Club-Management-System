# routes/auth.py

from flask import Blueprint, request, jsonify, session, redirect
from db import get_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    name = data.get('name')
    mobile_no = data.get('mobile_no')
    password = data.get('password')
    role = data.get('role')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        INSERT INTO users (name, mobile_no, password, role)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (name, mobile_no, password, role))
        conn.commit()
        
        return jsonify({"message": "User registered successfully"}), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    finally:
        cursor.close()
        conn.close()

@auth_bp.route('/login', methods=['POST'])



def login():
    try:
        data = request.get_json()
        print("DATA:", data)

        mobile_no = data.get('mobile_no')
        password = data.get('password')

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE mobile_no = %s",
            (str(mobile_no),)
        )
        user = cursor.fetchone()

        if user and user["password"] == password:
            session["user_id"] = user["user_id"]
            return jsonify({"message": "Login successful"})
        else:
            return jsonify({"message": "Invalid credentials"}), 401

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect('/')