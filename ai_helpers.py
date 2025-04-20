# ai_helpers.py
import re, json, logging, requests
from config import OR_API_KEY, OR_MODEL, OR_ENDPOINT
from xp_utils import ALL_STATS

def openrouter_chat(messages, temperature=0.3):
    # … your existing code unchanged …
    pass

def split_activities(daily_log: str):
    # Split on commas, semicolons, or the word "and"
    parts = re.split(r'[\,\;\.]\s*|\sand\s', daily_log)
    return [p.strip() for p in parts if p.strip()]

def match_skill(activity: str, skills: dict):
    """
    Return a skill name if any of its meta tags appear in the activity text.
    """
    lower = activity.lower()
    for name, info in skills.items():
        for tag in info.get("meta", []):
            if tag and tag.lower() in lower:
                return name
    return None

def suggest_xp(daily_log: str, character: dict):
    """
    1) Split daily_log into activities.
    2) Match each activity to character['skills'] via meta keywords.
    3) Ask the LLM only to assign stat_xp per activity.
    4) skill_xp = sum(stat_xp) if skill matched, else 0.
    Returns: [ {activity, stat_xp, skill, skill_xp}, … ]
    """
    # 1) Parse and match
    acts = split_activities(daily_log)
    base = []
    for act in acts:
        sk = match_skill(act, character.get("skills", {}))
        base.append({"activity": act, "skill": sk})

    # 2) Build LLM prompt for stat XP only
    system = """
You are LifeQuest‑AI. Given a list of activities, assign stat XP for each.
Stats: vitality, love, resilience, intelligence, willpower, flow, purpose, courage, joy, strength.
Rules:
- Use multiples of 5 XP.
- Return JSON: { "suggestions": [ { "activity": "...", "stat_xp": {stat: xp, ...} }, … ] }
- Only include stats with non‑zero XP.
"""
    user = json.dumps({"activities": acts}, ensure_ascii=False)

    raw = openrouter_chat([
        {"role":"system", "content": system},
        {"role":"user",   "content": user}
    ])

    # 3) Parse out stat_xp
    # raw may be dict or JSON string
    if isinstance(raw, str):
        cleaned = re.sub(r'^```(?:json)?\n?(.*?)```$', r'\1', raw, flags=re.DOTALL)
        data = json.loads(cleaned)
    else:
        data = raw
    llm_sugs = data.get("suggestions", [])

    # 4) Merge with base (skills) & compute skill_xp
    final = []
    for b in base:
        # find matching LLM suggestion
        match = next((x for x in llm_sugs if x["activity"] == b["activity"]), {})
        stats = match.get("stat_xp", {})
        skxp = sum(stats.values()) if b["skill"] else 0
        final.append({
            "activity": b["activity"],
            "stat_xp": stats,
            "skill": b["skill"],
            "skill_xp": skxp
        })
    return final
