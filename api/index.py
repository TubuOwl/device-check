from flask import Flask, request, jsonify, render_template_string
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# Database connection
def get_db_connection():
    # Adding sslmode for Neon DB
    database_url = os.environ.get('DATABASE_URL')
    if database_url and 'sslmode' not in database_url:
        if '?' in database_url:
            database_url += '&sslmode=require'
        else:
            database_url += '?sslmode=require'
    
    conn = psycopg2.connect(database_url)
    return conn

# Create table if not exists
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS user_fingerprints (
                id SERIAL PRIMARY KEY,
                fingerprint TEXT NOT NULL,
                user_agent TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error initializing database: {e}")

# Initialize database at startup
with app.app_context():
    init_db()

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fingerprint Tracker</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fingerprintjs2/2.1.0/fingerprint2.min.js"></script>
    <style>
        :root { --primary: #2563eb; --success: #22c55e; --bg: #f8fafc; --card: #ffffff; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background-color: var(--bg); color: #1e293b; }
        .container { background: var(--card); padding: 2.5rem; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); text-align: center; width: 100%; max-width: 400px; }
        h1 { color: var(--primary); margin-top: 0; font-size: 1.5rem; }
        #status { font-weight: 500; margin: 1.5rem 0; color: #64748b; }
        #result { color: var(--success); font-size: 0.875rem; min-height: 1.25rem; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid var(--primary); border-radius: 50%; width: 24px; height: 24px; animation: spin 1s linear infinite; margin: 0 auto 1rem; display: none; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #status.loading ~ .spinner { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner" id="spinner"></div>
        <h1>Fingerprint Tracker</h1>
        <p id="status" class="loading">Memproses identitas perangkat...</p>
        <div id="result"></div>
    </div>

    <script>
        function updateStatus(text, isLoading) {
            const status = document.getElementById('status');
            const spinner = document.getElementById('spinner');
            status.innerText = text;
            if (isLoading) {
                status.classList.add('loading');
                spinner.style.display = 'block';
            } else {
                status.classList.remove('loading');
                spinner.style.display = 'none';
            }
        }

        function getFingerprint() {
            Fingerprint2.get(function (components) {
                const values = components.map(function (component) { return component.value });
                const murmur = Fingerprint2.x64hash128(values.join(''), 31);
                
                updateStatus('Fingerprint Berhasil Dibuat', false);
                
                fetch('/save-fingerprint', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ fingerprint: murmur }),
                })
                .then(res => res.json())
                .then(data => {
                    document.getElementById('result').innerText = 'Data tersimpan di database!';
                })
                .catch(err => {
                    console.error('Error:', err);
                    document.getElementById('result').innerText = 'Gagal menyimpan data.';
                });
            });
        }

        if (window.requestIdleCallback) {
            requestIdleCallback(getFingerprint);
        } else {
            setTimeout(getFingerprint, 500);
        }
    </script>
</body>
</html>
''')

@app.route('/save-fingerprint', methods=['POST'])
def save_fingerprint():
    data = request.json
    fingerprint = data.get('fingerprint')
    user_agent = request.headers.get('User-Agent')
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]

    if not fingerprint:
        return jsonify({"error": "No fingerprint provided"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_fingerprints (fingerprint, user_agent, ip_address) VALUES (%s, %s, %s)",
            (fingerprint, user_agent, ip_address)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Fingerprint saved successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
