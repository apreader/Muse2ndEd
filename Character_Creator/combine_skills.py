import re
import random
from library_manager import fill_skill_placeholders

STANDARD_SKILLS = {
    "Athletics": "SOM", "Deceive": "SAV", "Fray": "REFx2", "Free Fall": "SOM",
    "Guns": "REF", "Infiltrate": "REF", "Infosec": "COG", "Interface": "COG",
    "Kinesics": "SAV", "Melee": "SOM", "Perceive": "INTx2", "Persuade": "SAV",
    "Program": "COG", "Provoke": "SAV", "PSI": "WIL", "Research": "INT",
    "Survival": "INT", "Hardware": "COG", "Medicine": "COG", "Pilot": "REF"
}

# Pools used when we must invent a subtype (no choices provided upstream)
CATEGORY_POOLS = {
    "Hardware": ["Aerospace", "Armorer", "Electronics", "Industrial", "Robotics", "Demolitions", "Groundcraft"],
    "Pilot": ["Air", "Ground", "Nautical", "Space", "Exotic Vehicle"],
    "Medicine": ["Biotech", "Forensics", "Paramedic", "Psychosurgery", "Veterinary"],
}

# Acceptable tokens in "Base Field" space-form seen in your JSON
VALID_FIELDS = {
    "Hardware": set(CATEGORY_POOLS["Hardware"]),
    "Pilot": set(["Air", "Ground", "Nautical", "Space", "Exotic", "Exotic Vehicle", "Groundcraft"]),
    "Medicine": set(CATEGORY_POOLS["Medicine"]),
    "Knowledge": None,  # any label allowed
}

def _normalize_skill_key(s: str) -> str:
    s = s.strip()

    # Only expand the whole word "Know" at the start, never "Knowledge"
    s = re.sub(r'^know\b', 'Knowledge', s, count=1, flags=re.I)

    # Already parenthesized — normalize base if it's Knowledge
    if "(" in s and ")" in s:
        base, field = s.split("(", 1)
        base = base.strip()
        field = field.strip(" )")
        if base.lower().startswith("knowledge"):
            return f"Knowledge ({field})"
        return f"{base} ({field})"

    # Colon form: "Base: Field" -> "Base (Field)"
    if ":" in s:
        base, field = s.split(":", 1)
        base, field = base.strip(), field.strip()
        if base.lower() == "know":
            base = "Knowledge"
        return f"{base} ({field})"

    # Space form (seen in your Backgrounds, e.g., "Pilot Ground")
    parts = s.split()
    if len(parts) >= 2:
        base = parts[0]
        field = " ".join(parts[1:])
        if base == "Faction" and parts[1] == "Knowledge":
            return f"Knowledge (Faction: {' '.join(parts[2:])})"
        for candidate in ("Hardware", "Pilot", "Medicine", "Knowledge"):
            if base.lower() == candidate.lower():
                if candidate == "Knowledge" or (VALID_FIELDS[candidate] and field in VALID_FIELDS[candidate]):
                    return f"{candidate} ({field})"

    # Bare "Knowledge" with no subtype — leave as-is
    if s.lower() == "knowledge":
        return "Knowledge"

    return s


def combine_skills(lm, background_skills, career_skills, interest_skills, faction_name, aptitudes, choice_skills_list=None):
    background_skills = background_skills or {}
    career_skills = career_skills or {}
    interest_skills = interest_skills or {}
    choice_skills_list = choice_skills_list or []

    # Resolve (Choose One) placeholders
    if choice_skills_list:
        background_skills = fill_skill_placeholders(background_skills, choice_skills_list)
        career_skills = fill_skill_placeholders(career_skills, choice_skills_list)
        interest_skills = fill_skill_placeholders(interest_skills, choice_skills_list)

    combined = {}

    # Merge with normalization up front
    for skill_dict in (background_skills, career_skills, interest_skills):
        for raw_skill, val in skill_dict.items():
            if isinstance(val, dict):
                continue
            if isinstance(val, list):
                print(f"Warning: skill '{raw_skill}' has list value {val} - skipping")
                continue
            if not isinstance(val, (int, float)):
                print(f"Warning: skill '{raw_skill}' has non-numeric value {val} - skipping")
                continue
            skill = _normalize_skill_key(raw_skill)
            combined[skill] = combined.get(skill, 0) + val

    # Assign subtypes to bare categories
    for base in ("Hardware", "Pilot", "Medicine"):
        if base in combined:
            pool = CATEGORY_POOLS.get(base, [])
            if pool:
                chosen = random.choice(pool)
                combined[f"{base} ({chosen})"] = combined.pop(base)

    # Add faction knowledge
    faction_skill = f"Knowledge (Faction: {faction_name})"
    combined[faction_skill] = combined.get(faction_skill, 0) + 30

    # Apply aptitude bases
    for skill_prefix, apt in STANDARD_SKILLS.items():
        if "x2" in apt:
            base_apt = apt.replace("x2", "")
            base_val = aptitudes.get(base_apt, 0) * 2
        else:
            base_val = aptitudes.get(apt, 0)

        matched = False
        for skill in list(combined.keys()):
            if skill.startswith(skill_prefix):
                combined[skill] += base_val
                matched = True
        if not matched:
            if skill_prefix in CATEGORY_POOLS:
                default_field = CATEGORY_POOLS[skill_prefix][0]
                key = f"{skill_prefix} ({default_field})"
            else:
                key = skill_prefix
            combined[key] = combined.get(key, 0) + base_val

    # Cap at 80 and redistribute overflow
    sorted_skills = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    skills_dict = dict(sorted_skills)

    overflow_pool = 0
    for k, v in list(skills_dict.items()):
        if v > 80:
            overflow = v - 80
            skills_dict[k] = 80
            overflow_pool += overflow

    while overflow_pool > 0:
        below_80 = [(s, v) for s, v in skills_dict.items() if v < 80]
        if not below_80:
            break
        below_80.sort(key=lambda x: x[1], reverse=True)
        for s, v in below_80:
            add = min(80 - v, overflow_pool)
            if add <= 0:
                continue
            skills_dict[s] = v + add
            overflow_pool -= add
            if overflow_pool <= 0:
                break

    # Final normalization pass + safety net against any lingering "Knowledgeledge"
    formatted_skills = {}
    for k, v in skills_dict.items():
        nk = _normalize_skill_key(k)
        nk = re.sub(r'^knowledge(?:ledge|knowledge)\b', 'Knowledge', nk, flags=re.I)
        formatted_skills[nk] = max(v, formatted_skills.get(nk, 0))

    return formatted_skills
