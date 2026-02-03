from flask import Flask, request, jsonify
import psycopg2
import os
import json
import urllib.parse

app = Flask(__name__)

# ================= DATABASE =================
def get_db():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL not set")

    if "sslmode" not in db_url:
        db_url += "?sslmode=require"

    return psycopg2.connect(db_url)

# ================= API (IMG BEACON) =================
@app.route("/api/check")
def check():
    try:
        raw = request.args.get("d")
        if not raw:
            return "no data", 400

        data = json.loads(urllib.parse.unquote(raw))

        username = data.get("name")
        device_id = data.get("id")
        ua = data.get("ua")
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO device_records
            (username, device_id, user_agent, ip_address)
            VALUES (%s, %s, %s, %s)
            """,
            (username, device_id, ua, ip)
        )
        conn.commit()
        cur.close()
        conn.close()

        # response HARUS image-safe
        return "", 204

    except Exception as e:
        print("ERROR:", e)
        return "", 204

@app.route("/api/whitelist")
def whitelist():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT username, device_id, user_agent, ip_address, created_at
        FROM device_records
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "username": r[0],
            "device_id": r[1],
            "user_agent": r[2],
            "ip": r[3],
            "created_at": r[4].isoformat()
        })

    return jsonify(result)


if __name__ == "__main__":
    app.run()
