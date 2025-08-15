import re

APTITUDE_KEYS = ["COG", "INT", "REF", "SAV", "SOM", "WIL"]

# Known Active & Knowledge skill patterns (broad, not exhaustive)
SKILL_PREFIXES = [
    # Core active
    "Athletics", "Deceive", "Fray", "Free Fall", "Guns", "Infiltrate", "Infosec",
    "Interface", "Kinesics", "Melee", "Perceive", "Persuade", "Program", "Provoke",
    "PSI", "Research", "Survival",
    # Families with specializations
    "Hardware", "Medicine", "Pilot", "Knowledge", "Academics", "Art", "Profession", "Language", "Science",
]

REP_KEYS = {"c-rep","f-rep","g-rep","i-rep","r-rep","x-rep","@-rep"}

OTHER_STAT_KEYS = {
    "Initiative","Lucidity","Trauma Threshold","Insanity Rating","Stress Taken","Traumas Taken",
    "Damage Taken","Wounds Taken","Insight","Moxie","Vigor","Wound Threshold","Durability",
    "Death Rating","Ego Flex","Flex","Starting Rez","Movement Rate","Ware","Morph"
}

def looks_like_skill(label: str) -> bool:
    lab = label.strip()
    if any(lab.startswith(p) for p in SKILL_PREFIXES):
        return True
    # Knowledge (Faction: Titanian) etc.
    if re.match(r"^Knowledge\s*\(.+\)$", lab, re.I):
        return True
    return False

def parse_character_txt(path):
    """Parse Muse TXT into structured dict with Aptitudes, Skills, Other Stats."""
    data = {"Aptitudes":{}, "Skills":{}, "Other Stats":{}}
    section = None
    with open(path, "r", encoding="utf-8-sig") as f:
        lines = [ln.rstrip("\n") for ln in f]

    # Track whether inside Focus Skills section to bias parsing
    inside_focus_skills = False

    for raw in lines:
        s = raw.strip()
        if not s:
            continue

        # Detect section headers (loose)
        if s.endswith(":") and ":" not in s[:-1]:
            header = s[:-1].strip().lower()
            inside_focus_skills = (header in ("focus skills","skills"))
            continue

        # Parse "Key: Value" lines
        if ":" in s:
            key, val = s.split(":", 1)
            key = key.strip()
            val = val.strip()

            # Try int conversion
            ival = None
            try:
                ival = int(val)
            except Exception:
                pass

            # Aptitudes whitelist
            if key in APTITUDE_KEYS and ival is not None:
                data["Aptitudes"][key] = ival
                continue

            # Other Stats known keys
            if (key in OTHER_STAT_KEYS or key in REP_KEYS) and ival is not None:
                data["Other Stats"][key] = ival
                continue

            # If in the skills section, treat as skill if numeric
            if inside_focus_skills and ival is not None:
                data["Skills"][key] = ival
                continue

            # Otherwise, only treat as skill if it looks like one and numeric
            if looks_like_skill(key) and ival is not None:
                data["Skills"][key] = ival
                continue

            # If numeric and neither aptitude/skill, file under Other Stats
            if ival is not None:
                data["Other Stats"][key] = ival
                continue

            # Non-numeric lines are ignored for now (name, background text, etc.)

    return data

def serialize_character_txt(char: dict) -> str:
    """Write a clean session file without overwriting the original format.
    Sections: Aptitudes / Focus Skills / Other Stats
    """
    lines = []
    lines.append("Aptitudes:")
    for k in ["COG","INT","REF","SAV","SOM","WIL"]:
        if k in char.get("Aptitudes",{}):
            lines.append(f"  {k}: {char['Aptitudes'][k]}")

    lines.append("")
    lines.append("Focus Skills:")
    for k in sorted(char.get("Skills",{}).keys()):
        lines.append(f"  {k}: {char['Skills'][k]}")

    lines.append("")
    lines.append("Other Stats:")
    for k,v in char.get("Other Stats",{}).items():
        lines.append(f"  {k}: {v}")

    return "\\n".join(lines) + "\\n"
