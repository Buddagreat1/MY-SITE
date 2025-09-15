# app.py
import os
import json
import uuid
from flask import Flask, render_template, request, jsonify

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

# ---------- Run (Render-ready) ----------
if __name__ == "__main__":
    # Render (and many PaaS) provide PORT via environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
