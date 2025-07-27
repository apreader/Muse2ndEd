STANDARD_SKILLS = {
    "Athletics": "SOM", "Deceive": "SAV", "Fray": "REFx2", "Free Fall": "SOM",
    "Guns": "REF", "Infiltrate": "REF", "Infosec": "COG", "Interface": "COG",
    "Kinesics": "SAV", "Melee": "SOM", "Perceive": "INTx2", "Persuade": "SAV",
    "Program": "COG", "Provoke": "SAV", "PSI": "WIL", "Research": "INT",
    "Survival": "INT", "Hardware": "COG", "Medicine": "COG", "Pilot": "REF"
}


def combine_skills(background_skills, career_skills, interest_skills, faction_name, aptitudes):
    combined = {}

    # Merge all skills from background, career, and interest
    for skill_dict in (background_skills, career_skills, interest_skills):
        for skill, val in skill_dict.items():
            if isinstance(val, dict):  # Skip nested skill dicts like "Know": {"Choose One": 40}
                continue
            combined[skill] = combined.get(skill, 0) + val

    # Add Faction Knowledge skill
    faction_skill = f"Faction Knowledge: {faction_name}"
    combined[faction_skill] = combined.get(faction_skill, 0) + 30

    # Apply aptitude bonuses
    for skill_prefix, apt in STANDARD_SKILLS.items():
        base_val = 0
        if "x2" in apt:
            apt = apt.replace("x2", "")
            base_val = aptitudes.get(apt, 0) * 2
        else:
            base_val = aptitudes.get(apt, 0)

        matched = False
        for skill in combined:
            if skill.startswith(skill_prefix):
                combined[skill] += base_val
                matched = True
        if not matched:
            combined[skill_prefix] = base_val

    # Cap skills at 80 and redistribute overflow
    sorted_skills = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    skills_dict = dict(sorted_skills)

    overflow_pool = 0
    for skill, val in skills_dict.items():
        if val > 80:
            overflow = val - 80
            skills_dict[skill] = 80
            overflow_pool += overflow

    while overflow_pool > 0:
        below_80 = [(s, v) for s, v in skills_dict.items() if v < 80]
        if not below_80:
            break
        below_80.sort(key=lambda x: x[1], reverse=True)

        for skill, val in below_80:
            add = min(80 - val, overflow_pool)
            skills_dict[skill] += add
            overflow_pool -= add
            if overflow_pool <= 0:
                break

    return skills_dict
