from flask import Flask, jsonify
import psycopg2
import os
import traceback

app = Flask(__name__)

@app.route("/")
def index():
    try:
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return jsonify({
                "ok": False,
                "error": "DATABASE_URL not set"
            }), 500

        # Neon WAJIB SSL
        if "sslmode=" not in db_url:
            db_url += ("&" if "?" in db_url else "?") + "sslmode=require"

        # CONNECT TEST
        conn = psycopg2.connect(
            db_url,
            connect_timeout=5
        )
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()

        return jsonify({
            "ok": True,
            "message": "Flask connected to Neon Postgres"
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500
