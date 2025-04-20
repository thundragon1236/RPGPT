# app.py
import os, json
from datetime import date
from flask import Flask, request, jsonify
from ai_helpers import suggest_xp, match_skill  # import if needed
from xp_utils import add_xp_to_bucket
from config import DATA_DIR  # define DATA_DIR = "data" in config

# ─ Setup ─────────────────────────────────
os.makedirs(DATA_DIR, exist_ok=True)
app = Flask(__name__)

def paths_for(char_id):
    d = os.path.join(DATA_DIR, char_id)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "logs.json"), os.path.join(d, "stats.json")

def load_character(char_id):
    _, stats_p = paths_for(char_id)
    if os.path.exists(stats_p):
        return json.load(open(stats_p))
    return {"stats": {}, "skills": {}}

def save_character(char_id, character):
    _, stats_p = paths_for(char_id)
    with open(stats_p, "w") as f:
        json.dump(character, f, indent=2)

def append_log(char_id, entry):
    logs_p, _ = paths_for(char_id)
    logs = json.load(open(logs_p)) if os.path.exists(logs_p) else []
    logs.append(entry)
    with open(logs_p, "w") as f:
        json.dump(logs, f, indent=2)

# ─ Endpoints ─────────────────────────────────

@app.route("/suggest_xp", methods=["POST"])
def route_suggest():
    data         = request.json
    log_text     = data["daily_log"]
    char_id      = data.get("character_id", "default")
    character    = load_character(char_id)
    suggestions  = suggest_xp(log_text, character)
    return jsonify({"suggestions": suggestions})

@app.route("/save_progress", methods=["POST"])
def route_save():
    data         = request.json
    char_id      = data["character_id"]
    log_text     = data.get("daily_log", "")
    suggestions  = data["suggestions"]

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
    char_id = request.args["character_id"]
    char    = load_character(char_id)
    return jsonify({"skills": char.get("skills", {})})

@app.route("/get_stats", methods=["GET"])
def route_get_stats():
    char_id = request.args["character_id"]
    char    = load_character(char_id)
    return jsonify({"stats": char.get("stats", {})})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",5000)))
