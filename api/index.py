from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

# ================= DB CONNECTION =================
def get_conn():
    db = os.environ.get("DATABASE_URL")
    if not db:
        raise Exception("DATABASE_URL not set")

    if "sslmode=" not in db:
        db += ("&" if "?" in db else "?") + "sslmode=require"

    return psycopg2.connect(db)

# ================= CORS =================
@app.after_request
def cors(res):
    res.headers["Access-Control-Allow-Origin"] = "*"
    res.headers["Access-Control-Allow-Headers"] = "Content-Type"
    res.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return res

# ================= API =================
@app.route("/api/check", methods=["POST", "OPTIONS"])
def check():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}

    name = data.get("name", "Anon")
    fingerprint = data.get("id")
    ua = data.get("ua")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    if not fingerprint:
        return jsonify({"ok": False, "error": "missing fingerprint"}), 400

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO user_records
        (chatango_name, fingerprint, user_agent, ip_address)
        VALUES (%s, %s, %s, %s)
    """, (name, fingerprint, ua, ip))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"ok": True})

# ================= LOCAL RUN =================
if __name__ == "__main__":
    app.run(debug=True)
