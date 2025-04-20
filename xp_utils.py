# xp_utils.py

# ── New doubling thresholds per your spec:
SKILL_TIER_THRESHOLDS = [
    (0,   "F"),  # always
    (5,   "E"),  # after 5 levels (i.e. 500 XP)
    (10,  "D"),  # after 10 levels
    (20,  "C"),
    (40,  "B"),
    (80,  "A"),
    (160, "S"),
    (320, "SS")
]

def compute_skill_tier(level):
    for thresh, tier in reversed(SKILL_TIER_THRESHOLDS):
        if level >= thresh:
            return tier
    return "F"

def add_xp_to_bucket(bucket, key, delta_xp, parent=None):
    """
    bucket: dict of stats or skills
    key: stat/skill name
    delta_xp: integer XP to add
    Returns (old_tier, new_tier) for skills if tier changed, else None
    """
    if key not in bucket:
        # skills have 'meta' & 'flavour'; stats do not
        if any(isinstance(v, dict) and "meta" in v for v in bucket.values()):
            bucket[key] = {"xp": 0, "level": 0, "meta": [], "flavour": "", "tier": "F"}
        else:
            bucket[key] = {"xp": 0, "level": 0}

    rec = bucket[key]
    rec["xp"]   += delta_xp
    rec["level"] = rec["xp"] // 100  # 100 XP per level

    # Only skills get tiers
    if "meta" in rec:
        old_t = rec.get("tier", "F")
        new_t = compute_skill_tier(rec["level"])
        rec["tier"] = new_t
        if new_t != old_t:
            return old_t, new_t
    return None

# All stats list for reference
ALL_STATS = [
    "vitality","love","resilience","intelligence",
    "willpower","flow","purpose","courage","joy","strength"
]
