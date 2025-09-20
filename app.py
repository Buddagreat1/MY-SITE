from flask import Flask, render_template, request, jsonify
import json, os, uuid, socket

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
@app.route("/heroes")
def heroes():
    return jsonify(load_json(HEROES_FILE, []))

@app.route("/add", methods=["POST"])
def add():
    heroes = load_json(HEROES_FILE, [])
    new_hero = {"id": str(uuid.uuid4()), "name": "", "level": "", "power": ""}
    heroes.append(new_hero)
    save_json(HEROES_FILE, heroes)
    return jsonify(new_hero)

@app.route("/update", methods=["POST"])
def update():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(error="Invalid JSON"), 400

    heroes = load_json(HEROES_FILE, [])
    for hero in heroes:
        if hero["id"] == data.get("id"):
            if data["field"] in {"name", "level", "power"}:
                hero[data["field"]] = data["value"]

    save_json(HEROES_FILE, heroes)
    return jsonify(success=True)

@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(error="Invalid JSON"), 400

    heroes = load_json(HEROES_FILE, [])
    updated = [h for h in heroes if h["id"] != data.get("id")]
    save_json(HEROES_FILE, updated)
    return jsonify(success=True)

# ---------- Progression ----------
@app.route("/progression")
def get_progression():
    return jsonify(load_json(PROGRESSION_FILE, {
        "wins": 0,
        "losses": 0,
        "stages_cleared": 0,
        "achievements": []
    }))

@app.route("/progression/update", methods=["POST"])
def update_progression():
    data = request.get_json(silent=True)
    if not data:
        return jsonify(error="Invalid JSON"), 400

    progression = load_json(PROGRESSION_FILE, {
        "wins": 0,
        "losses": 0,
        "stages_cleared": 0,
        "achievements": []
    })

    for key in ["wins", "losses", "stages_cleared", "achievements"]:
        if key in data:
            progression[key] = data[key]

    save_json(PROGRESSION_FILE, progression)
    return jsonify(success=True)

@app.route("/progression/reset", methods=["POST"])
def reset_progression():
    progression = {
        "wins": 0,
        "losses": 0,
        "stages_cleared": 0,
        "achievements": []
    }
    save_json(PROGRESSION_FILE, progression)
    return jsonify(success=True, progression=progression)

# ---------- Frontend ----------
@app.route("/")
def home():
    return render_template("index.html")

# ---------- Port Finder ----------
def find_free_port(start_port=5000, max_port=5100):
    port = start_port
    while port <= max_port:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    raise RuntimeError("No free ports available in range 5000–5100")

# ---------- Main ----------
if __name__ == "__main__":
    port = find_free_port()
    print(f"✅ Starting Flask on port {port}")
    app.run(debug=True, port=port)
