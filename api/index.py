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

# Init DB (safe for serverless)
try:
    init_db()
except Exception as e:
    print("DB init error:", e)

# ================= ROUTES =================
@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Fingerprint Tracker</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/fingerprintjs2/2.1.0/fingerprint2.min.js"></script>
</head>
<body>
<h3>Fingerprinting...</h3>
<script>
Fingerprint2.get(function(components){
    const values = components.map(c => c.value).join("");
    const hash = Fingerprint2.x64hash128(values, 31);

    fetch("/api/save-fingerprint", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ fingerprint: hash })
    }).then(()=>document.body.innerHTML="Device recorded ✔");
});
</script>
</body>
</html>
""")

@app.route("/save-fingerprint", methods=["POST"])
def save_fingerprint():
    data = request.json
    fingerprint = data.get("fingerprint")
    if not fingerprint:
        return jsonify({"error":"missing fingerprint"}), 400

    ua = request.headers.get("User-Agent")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO user_fingerprints (fingerprint, user_agent, ip_address) VALUES (%s,%s,%s)",
        (fingerprint, ua, ip)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"ok":True})
