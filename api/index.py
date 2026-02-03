from flask import Flask, jsonify
import psycopg2
import os
import traceback

app = Flask(__name__)

def get_conn():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL not set")

    # Neon wajib SSL
    if "sslmode=" not in db_url:
        db_url += ("&" if "?" in db_url else "?") + "sslmode=require"

    return psycopg2.connect(db_url, connect_timeout=5)

@app.route("/")
def create_table():
    try:
        conn = get_conn()
        cur = conn.cursor()

        # TABLE UNTUK RECORD DATA USER
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_records (
                id SERIAL PRIMARY KEY,
                fingerprint TEXT,
                user_agent TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "ok": True,
            "message": "Table user_records created (or already exists)"
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500
