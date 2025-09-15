# ----- app.py ----- #
from flask import Flask, render_template, request, jsonify
import json, os, uuid, webbrowser, socket, subprocess, signal
from threading import Timer
from pyngrok import ngrok

app = Flask(__name__)

# ---------- Files ----------
HEROES_FILE = "heroes.json"
PROGRESSION_FILE = "progression.json"

# ---------- Helpers ----------
def load_json(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# ---------- Heroes ----------
def load_heroes():
    return load_json(HEROES_FILE, [])

def save_heroes(heroes):
    save_json(HEROES_FILE, heroes)

@app.route("/heroes")
def heroes():
    return jsonify(load_heroes())

@app.route("/add", methods=["POST"])
def add():
    heroes = load_heroes()
    new_hero = {"id": str(uuid.uuid4()), "name": "", "level": "", "power": ""}
    heroes.append(new_hero)
    save_heroes(heroes)
    return jsonify(new_hero)

@app.route("/update", methods=["POST"])
def update():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(error="Invalid JSON"), 400

    allowed_fields = {"name", "level", "power"}
    heroes = load_heroes()
    for hero in heroes:
        if hero["id"] == data.get("id"):
            if data["field"] in allowed_fields:
                hero[data["field"]] = data["value"]

    save_heroes(heroes)
    return jsonify(success=True)

@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(error="Invalid JSON"), 400

    heroes = load_heroes()
    updated = [h for h in heroes if h["id"] != data.get("id")]
    save_heroes(updated)
    return jsonify(success=True)

# ---------- Game Progression ----------
def load_progression():
    default = {
        "wins": 0,
        "losses": 0,
        "stages_cleared": 0,
        "achievements": []
    }
    return load_json(PROGRESSION_FILE, default)

def save_progression(progression):
    save_json(PROGRESSION_FILE, progression)

@app.route("/progression")
def get_progression():
    return jsonify(load_progression())

@app.route("/progression/update", methods=["POST"])
def update_progression():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(error="Invalid JSON"), 400

    progression = load_progression()

    # Update only known fields
    for key in ["wins", "losses", "stages_cleared", "achievements"]:
        if key in data:
            progression[key] = data[key]

    save_progression(progression)
    return jsonify(success=True)

@app.route("/progression/reset", methods=["POST"])
def reset_progression():
    progression = {
        "wins": 0,
        "losses": 0,
        "stages_cleared": 0,
        "achievements": []
    }
    save_progression(progression)
    return jsonify(success=True, progression=progression)

# ---------- Frontend ----------
@app.route("/")
def index():
    return render_template("index.html")

# ---------- Port Management ----------
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def kill_process_on_port(port):
    try:
        result = subprocess.check_output(
            ["lsof", "-t", f"-i:{port}"], text=True
        ).strip()
        if result:
            for pid in result.split("\n"):
                os.kill(int(pid), signal.SIGKILL)
            print(f"💀 Killed process(es) on port {port}")
    except subprocess.CalledProcessError:
        pass  # nothing running

def find_free_port(start_port=5000):
    port = start_port
    while is_port_in_use(port):
        port += 1
    return port

# ---------- Auto-open Browser ----------
def open_browser(url):
    webbrowser.open_new(url)

if __name__ == "__main__":
    PORT = 5000

    # Kill any process using 5000
    if is_port_in_use(PORT):
        kill_process_on_port(PORT)

    # If still busy, find a free one
    if is_port_in_use(PORT):
        PORT = find_free_port(5000)

    # Start ngrok tunnel
    public_url = ngrok.connect(PORT, "http").public_url
    skip_url = f"{public_url}?ngrok-skip-browser-warning=true"

    print(f"\n🚀 Your site is live at:\n{public_url}\n(no-warning link: {skip_url})\n")

    # Open browser to skip-warning link
    Timer(1, open_browser, args=(skip_url,)).start()

    # Run Flask
    app.run(port=PORT, debug=False, use_reloader=False)
