from flask import Flask, request
import psycopg2, os, json, urllib.parse

app = Flask(__name__)

def get_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise Exception("DATABASE_URL not set")
    if "sslmode" not in url:
        url += "?sslmode=require"
    return psycopg2.connect(url)

@app.route("/api/check", methods=["GET"])
def check():
    try:
        raw = request.args.get("d")
        if not raw:
            return "", 204

        data = json.loads(urllib.parse.unquote(raw))

        name = data.get("name")
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
            (name, device_id, ua, ip)
        )
        conn.commit()
        cur.close()
        conn.close()

        # IMG beacon MUST return empty
        return "", 204

    except Exception as e:
        print("ERROR:", e)
        return "", 204

# === GET DATA JSON ===
@app.route("/api/whitelist")
def whitelist():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT username, device_id, user_agent, ip_address, created_at
        FROM device_records
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "username": r[0],
            "device_id": r[1],
            "user_agent": r[2],
            "ip": r[3],
            "created_at": r[4].isoformat()
        } for r in rows
    ])
