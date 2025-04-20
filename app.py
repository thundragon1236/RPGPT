# app.py
import os, json
from datetime import date
from flask import Flask, request, jsonify, abort
from ai_helpers import suggest_xp, match_skill  # import if needed
from xp_utils import add_xp_to_bucket
from config import DATA_DIR  # define DATA_DIR = "data" in config
import logging

# ─ Setup ─────────────────────────────────
os.makedirs(DATA_DIR, exist_ok=True)
app = Flask(__name__)

def paths_for(char_id):
    d = os.path.join(DATA_DIR, char_id)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "logs.json"), os.path.join(d, "stats.json")

def load_character(char_id):
    # Load character stats from stats.json under DATA_DIR/char_id
    _, stats_p = paths_for(char_id)
    if not os.path.exists(stats_p):
        return {"id": char_id, "stats": {}, "skills": {}}
    try:
        with open(stats_p, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"Malformed character file: {stats_p}")
        os.rename(stats_p, stats_p + ".bad")
        abort(500, description=f"Malformed character file: {stats_p}")

def save_character(char_id, character):
    _, stats_p = paths_for(char_id)
    with open(stats_p, "w") as f:
        json.dump(character, f, indent=2)

def append_log(char_id, entry):
    logs_p, _ = paths_for(char_id)
    try:
        if os.path.exists(logs_p):
            with open(logs_p, "r", encoding="utf-8") as f:
                logs = json.load(f)
        else:
            logs = []
    except json.JSONDecodeError:
        logging.error(f"Malformed log file: {logs_p}")
        os.rename(logs_p, logs_p + ".bad")
        abort(500, description=f"Malformed log file: {logs_p}")
    logs.append(entry)
    with open(logs_p, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

# ─ Endpoints ─────────────────────────────────

@app.route("/")
def index():
    return jsonify({"message": "LifeQuest GPT Backend is running."})

@app.route("/suggest_xp", methods=["POST"])
def route_suggest():
    data = request.get_json(force=True)
    log_text = data.get("daily_log")
    character = data.get("character")
    if not log_text or not character:
        return jsonify({"error": "Missing required field(s): daily_log and character are required."}), 400
    try:
        suggestions = suggest_xp(log_text, character)
    except Exception as e:
        return jsonify({"error": "AI error", "details": str(e)}), 502
    return jsonify({"suggestions": suggestions})

@app.route("/save_progress", methods=["POST"])
def route_save():
    data = request.get_json(force=True)
    char_id = data.get("character_id")
    log_text = data.get("daily_log")
    suggestions = data.get("suggestions")
    if not char_id or not log_text or suggestions is None:
        return jsonify({"error": "Missing required field(s): character_id, daily_log, suggestions"}), 400

    # 1) Append the raw log
    append_log(char_id, {"date": str(date.today()), "entry": log_text})

    # 2) Apply XP to stats & skills
    char = load_character(char_id)
    for s in suggestions:
        for st, xp in s["stat_xp"].items():
            add_xp_to_bucket(char["stats"], st, xp)
        if s["skill"]:
            add_xp_to_bucket(char["skills"], s["skill"], s["skill_xp"])
    save_character(char_id, char)

    return jsonify({"status": "saved"})

@app.route("/list_skills", methods=["GET"])
def route_list_skills():
    char_id = request.args.get("character_id")
    if not char_id:
        return jsonify({"error": "Missing required query parameter: character_id"}), 400
    char    = load_character(char_id)
    return jsonify({"skills": char.get("skills", {})})

@app.route("/get_stats", methods=["GET"])
def route_get_stats():
    char_id = request.args.get("character_id")
    if not char_id:
        return jsonify({"error": "Missing required query parameter: character_id"}), 400
    char    = load_character(char_id)
    return jsonify({"stats": char.get("stats", {})})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
