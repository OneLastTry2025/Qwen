# c:\Users\itspr\DailyQuest\Qwen\receive_auth_state.py
import json
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Path Setup ---
PROJECT_ROOT = Path(__file__).resolve().parent
STATE_FILE = PROJECT_ROOT / "storage_state.json"

app = Flask(__name__)
# This allows your Chrome extension to send data to this server.
CORS(app)

@app.route('/save_auth', methods=['POST'])
def save_auth():
    """Receives auth data from the extension and saves it to a file."""
    print("[*] Received authentication data from Chrome extension...")
    data = request.get_json()
    
    if not data:
        print("[!] ERROR: No data received from extension.")
        return jsonify({"status": "error", "message": "No data received"}), 400

    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"[+] Authentication state successfully saved to '{STATE_FILE}'")
        return jsonify({"status": "success", "message": "State saved successfully!"}), 200
    except Exception as e:
        print(f"[!] ERROR: Failed to write to state file: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("[*] Starting local server to receive auth state from extension...")
    print("[*] Listening on http://127.0.0.1:8000")
    print("[!] Keep this server running, then use the Chrome extension to save the session.")
    app.run(host='127.0.0.1', port=8000)