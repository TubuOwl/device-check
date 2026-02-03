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
                "status": "ERROR",
                "detail": "DATABASE_URL not set"
            }), 500

        # paksa ssl (Neon wajib)
        if "sslmode=" not in db_url:
            db_url += ("&" if "?" in db_url else "?") + "sslmode=require"

        # COBA CONNECT
        conn = psycopg2.connect(db_url, connect_timeout=5)
        conn.close()

        return jsonify({
            "status": "OK",
            "message": "Connected to PostgreSQL successfully"
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "ERROR",
            "detail": str(e)
        }), 500
