from flask import Flask, request, jsonify, render_template_string
import psycopg2
import os

app = Flask(__name__)

# ================= DATABASE =================
def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise Exception("DATABASE_URL not set")

    if "sslmode" not in database_url:
        database_url += "?sslmode=require"

    return psycopg2.connect(database_url)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_fingerprints (
            id SERIAL PRIMARY KEY,
            fingerprint TEXT NOT NULL,
            user_agent TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Init DB (serverless-safe)
try:
    init_db()
except Exception as e:
    print("DB init error:", e)

# ================= ROUTES =================

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Device Check</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/fingerprintjs2/2.1.0/fingerprint2.min.js"></script>
</head>
<body>
<h3>Recording device...</h3>

<script>
Fingerprint2.get(function(components){
    const raw = components.map(c => c.value).join("");
    const hash = Fingerprint2.x64hash128(raw, 31);

    fetch("/api/save-fingerprint", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ fingerprint: hash })
    })
    .then(r => r.json())
    .then(() => {
        document.body.innerHTML = "Device recorded ✔";
    })
    .catch(() => {
        document.body.innerHTML = "Error recording device";
    });
});
</script>
</body>
</html>
""")

# ===== CORE SAVE FUNCTION =====
def _save_fingerprint():
    data = request.get_json(silent=True) or {}
    fingerprint = data.get("fingerprint")

    if not fingerprint:
        return jsonify({"error": "fingerprint required"}), 400

    ua = request.headers.get("User-Agent")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = ip.split(",")[0] if ip else None

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_fingerprints (fingerprint, user_agent, ip_address) VALUES (%s, %s, %s)",
        (fingerprint, ua, ip)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok"})

# ===== ROUTE ALIASES =====
@app.route("/save-fingerprint", methods=["POST"])
def save_fp():
    return _save_fingerprint()

@app.route("/api/save-fingerprint", methods=["POST"])
def save_fp_api():
    return _save_fingerprint()

# ===== DEBUG =====
@app.route("/ping")
def ping():
    return "OK"
