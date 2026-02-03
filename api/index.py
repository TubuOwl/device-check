from flask import Flask, request, jsonify
import psycopg2
import psycopg2.errors
import os, json, urllib.parse

app = Flask(__name__)

# ================= DB =================
def get_db():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise Exception("DATABASE_URL not set")

    if "sslmode" not in url:
        url += "?sslmode=require"

    return psycopg2.connect(url)

# =================================================
# API 1️⃣ : RECORD DEVICE (IMG BEACON, ANTI DOUBLE)
# =================================================
@app.route("/api/check", methods=["GET"])
def check_device():
    try:
        raw = request.args.get("d")
        if not raw:
            return jsonify({"status": "no_data"}), 200

        data = json.loads(urllib.parse.unquote(raw))

        username = data.get("name")
        device_id = data.get("id")
        ua = data.get("ua")
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        if not device_id:
            return jsonify({"status": "no_device_id"}), 200

        conn = get_db()
        cur = conn.cursor()

        # 🔍 CEK DEVICE ID
        cur.execute(
            "SELECT id, username, created_at FROM device_records WHERE device_id=%s",
            (device_id,)
        )
        row = cur.fetchone()

        if row:
            cur.close()
            conn.close()
            return jsonify({
                "status": "exists",
                "device_id": device_id,
                "first_seen": row[2].isoformat()
            }), 200

        # ➕ INSERT JIKA BELUM ADA
        cur.execute(
            """
            INSERT INTO device_records
            (username, device_id, user_agent, ip_address)
            VALUES (%s, %s, %s, %s)
            RETURNING id, created_at
            """,
            (username, device_id, ua, ip)
        )

        new = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "status": "inserted",
            "id": new[0],
            "device_id": device_id,
            "created_at": new[1].isoformat()
        }), 201

    except psycopg2.errors.UniqueViolation:
        # safety net (kalau hit bersamaan)
        return jsonify({
            "status": "exists",
            "device_id": device_id
        }), 200

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"status": "error"}), 500


# =====================================
# API 2️⃣ : GET WHITELIST (JSON OUTPUT)
# =====================================
@app.route("/api/whitelist", methods=["GET"])
def whitelist():
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, username, device_id, user_agent, ip_address, created_at
            FROM device_records
            ORDER BY created_at DESC
        """)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        devices = []
        for r in rows:
            devices.append({
                "id": r[0],
                "username": r[1],
                "device_id": r[2],
                "user_agent": r[3],
                "ip_address": r[4],
                "created_at": r[5].isoformat()
            })

        return jsonify({
            "count": len(devices),
            "devices": devices
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run()
