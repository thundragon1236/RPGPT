# ai_helpers.py
import re, json, logging, requests
from config import OR_API_KEY, OR_MODEL, OR_ENDPOINT
from xp_utils import ALL_STATS

def openrouter_chat(messages, temperature=0.3):
    if not OR_API_KEY or not OR_MODEL:
        raise ValueError("OpenRouter API key/model not configured.")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OR_API_KEY}"
    }
    payload = {
        "model": OR_MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
        "response_format": {"type": "json_object"}
    }
    try:
        r = requests.post(OR_ENDPOINT, headers=headers, json=payload, timeout=90)
        r.raise_for_status()
        resp = r.json()
        content = resp["choices"][0]["message"]["content"]
        # Try parsing JSON out of the content string
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logging.warning("Couldn't parse AI response as JSON, returning raw string.")
            return content
    except Exception as e:
        logging.error(f"Error calling AI service: {e}")
        raise

def strip_markdown_fences(s):
    # Remove markdown code fences if present
    if isinstance(s, str):
        return re.sub(r'^```(?:json)?\n?(.*?)```$', r'\1', s, flags=re.DOTALL)
    return s

# ... rest of code unchanged ...

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
    if raw is None:
        logging.warning("No AI response, returning empty suggestions.")
        return []
    if isinstance(raw, str):
        cleaned = strip_markdown_fences(raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logging.warning("Couldn't parse AI response as JSON, returning empty suggestions.")
            return []
    else:
        data = raw
    llm_sugs = data.get("suggestions", [])

    # 4) Merge with base (skills) & compute skill_xp
    final = []
    for b in base:
        # find matching LLM suggestion
        match = next((x for x in llm_sugs if x.get("activity") == b["activity"]), {})
        stats = match.get("stat_xp", {})
        if not isinstance(stats, dict):
            logging.warning("Malformed AI response, skipping activity.")
            continue
        skxp = sum(stats.values()) if b["skill"] else 0
        final.append({
            "activity": b["activity"],
            "stat_xp": stats,
            "skill": b["skill"],
            "skill_xp": skxp
        })
    return final
