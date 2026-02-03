from flask import Flask, request, Response, jsonify
import psycopg2, os, json, base64

app = Flask(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]

def db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# === RECORD DEVICE (IMG BEACON) ===
@app.route("/api/check")
def check_device():
    d = request.args.get("d")
    if not d:
        return Response(status=204)

    try:
        data = json.loads(d)
    except:
        return Response(status=204)

    device_id = data.get("id")
    if not device_id:
        return Response(status=204)

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO device_records (username, device_id, user_agent, ip_address)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (device_id) DO NOTHING
    """, (
        data.get("name"),
        device_id,
        data.get("ua"),
        request.headers.get("X-Forwarded-For", request.remote_addr)
    ))

    conn.commit()
    cur.close()
    conn.close()

    return Response(b"", status=204)

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
