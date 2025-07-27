from flask import Flask, request, jsonify
from flask_cors import CORS
from db import init_db, get_db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)
init_db()

@app.route("/api/register", methods=["POST"])
def register():
    data = request.json
    print("💻 收到注册请求：", data)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400

    db = get_db()
    exists = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if exists:
        return jsonify({"success": False, "message": "用户名已存在"}), 409

    db.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, generate_password_hash(password))
    )
    db.commit()
    return jsonify({"success": True, "message": "注册成功"})

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user and check_password_hash(user["password"], password):
        return jsonify({
            "success": True,
            "user": {
                "username": user["username"]
            }
        })
    return jsonify({"success": False, "message": "用户名或密码错误"}), 401

if __name__ == "__main__":
    app.run(debug=True)
