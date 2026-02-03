from flask import Flask, jsonify
import psycopg2
import os
import traceback

app = Flask(__name__)

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL not set")

    # pastikan ssl
    if "sslmode=" not in db_url:
        db_url += ("&" if "?" in db_url else "?") + "sslmode=require"

    return psycopg2.connect(db_url, connect_timeout=5)

@app.route("/")
def index():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_fingerprints (
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
            "status": "OK",
            "message": "Table user_fingerprints created (or already exists)"
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "ERROR",
            "detail": str(e)
        }), 500
