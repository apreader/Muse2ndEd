import os
import re
from PyPDF2.generic import NameObject, BooleanObject

# ---------- Parsing config ----------
KNOWN_SECTIONS = {
    "Aptitudes",
    "Derived Stats",
    "Reputation Scores",
    "Focus Skills",
}
ALWAYS_TOP_LEVEL = {
    # Identity
    "Name", "Aliases", "Motivations", "Languages", "Ego Traits", "Faction",
    "Gender", "Sex", "Age", "Muse", "Career", "Interest",
    # Background + paragraph
    "Background",
    # Morph & tracks
    "Morph", "Movement Rate", "Ware",
    "Damage Taken", "Wounds Taken", "Insight", "Moxie", "Vigor",
    "Wound Threshold", "Durability", "Death Rating", "Ego Flex",
    # Pools & misc
    "Flex", "Starting Rez",
}

def parse_character_txt(path, debug=False):
    """
    - Only headers in KNOWN_SECTIONS open a section.
    - Keys in ALWAYS_TOP_LEVEL are always recorded at top level.
    - Captures Background description paragraph after 'Background:' into 'Background.Description'.
    """
    data = {}
    section = None
    capture_bg = False
    bg_lines = []

    with open(path, "r", encoding="utf-8-sig") as f:
        lines = [ln.rstrip("\n") for ln in f]

    def flush_bg():
        nonlocal capture_bg, bg_lines
        if capture_bg and bg_lines:
            data["Background.Description"] = " ".join(s.strip() for s in bg_lines if s.strip())
        capture_bg = False
        bg_lines = []

    for raw in lines:
        s = raw.strip()

        # blank line: may end background paragraph
        if not s:
            flush_bg()
            continue

        # section header only if whitelisted
        if s.endswith(":") and ":" not in s[:-1]:
            flush_bg()
            header = s[:-1]
            if header in KNOWN_SECTIONS:
                section = header
            else:
                data[header] = ""
                section = None
                if header.lower() == "background":
                    capture_bg = True
                    bg_lines = []
            continue

        # key: value
        if ":" in raw:
            key, value = raw.rsplit(":", 1)
            key = key.strip()
            value = value.strip()

            if key in ALWAYS_TOP_LEVEL:
                flush_bg()
                data[key] = value
                section = None
                if key.lower() == "background":
                    capture_bg = True
                    bg_lines = []
                continue

            if section in KNOWN_SECTIONS:
                data[f"{section}.{key}"] = value
            else:
                data[key] = value

            if section is None and key.lower() == "background":
                capture_bg = True
                bg_lines = []
            continue

        # paragraph text after Background:
        if capture_bg:
            bg_lines.append(raw)

    flush_bg()

    if debug:
        print(f"\n[DEBUG] Parsed {len(data)} keys from {os.path.basename(path)}:")
        for k in sorted(data.keys()):
            print(f"  - {k}: {data[k]}")
        print("")
    return data

# ---------- Knowledge helpers ----------

def _to_int(x, default=0):
    try:
        return int(str(x).strip())
    except Exception:
        return default

def knowledge_category_from_label(label):
    """
    Return canonical category:
      Academics, Art, Exotic Language, Interest, Language, Profession
    """
    t = str(label or "").strip()
    m = re.search(r'\(([^)]+)\)', t)
    inside = m.group(1) if m else t
    inside = inside.strip().lower()
    if inside.startswith("academics:"):
        return "Academics"
    if inside.startswith("art:"):
        return "Art"
    if inside.startswith("exotic language:"):
        return "Exotic Language"
    if inside.startswith("language:"):
        return "Language"
    if inside.startswith("interest:"):
        return "Interest"
    if inside.startswith("profession:"):
        return "Profession"
    return None

def knowledge_apt_and_total(label, base_value, src_dict):
    """
    Linked aptitude per category:
      COG: Academics, Interest, Profession
      INT: Art, Exotic Language, Language
    Total = base skill rating + linked aptitude
    Returns (apt_str, total_str)
    """
    cat = knowledge_category_from_label(label)
    cog = _to_int(src_dict.get("Aptitudes.COG"))
    itg = _to_int(src_dict.get("Aptitudes.INT"))

    if cat in ("Academics", "Interest", "Profession"):
        apt = "COG"
        total = _to_int(base_value) + cog
    elif cat in ("Art", "Exotic Language", "Language"):
        apt = "INT"
        total = _to_int(base_value) + itg
    else:
        apt = "COG"
        total = _to_int(base_value) + cog

    return apt, str(total)

def format_know_label(label):
    """
    Normalize to: Knowledge (<Category: Field>)
    Ensures faction-style categories get 'Faction: ' prefix inside.
    """
    t = re.sub(r'\s+', ' ', str(label)).strip()
    m = re.match(r'^(?:Faction\s+)?Knowledge\s*[\(:]\s*(.+?)\)?$', t, re.I)
    if m:
        inner = m.group(1).strip()
        if not inner.lower().startswith('faction:'):
            if re.match(r'^(Mercurial|Titanian|Jovian|Anarchist|Autonomist|Criminal|Hypercorp|Inner|Outer|Sifter)\b', inner, re.I):
                inner = f'Faction: {inner}'
        return f'Knowledge ({inner})'
    m = re.match(r'^Knowledge\s*\((.+?)\)$', t, re.I)
    if m:
        return f'Knowledge ({m.group(1).strip()})'
    m = re.match(r'^(?:Know|Knowledge)\s*[:\-]\s*(.+)$', t, re.I)
    if m:
        return f'Knowledge ({m.group(1).strip()})'
    if t.lower().startswith('faction:'):
        return f'Knowledge ({t})'
    return f'Knowledge ({t})'

# ---------- PDF helpers ----------

def enable_need_appearances(writer, reader):
    try:
        acro = reader.trailer["/Root"].get("/AcroForm")
        if acro is not None:
            writer._root_object.update({NameObject("/AcroForm"): acro})
            acro.update({NameObject("/NeedAppearances"): BooleanObject(True)})
    except Exception:
        pass  # non-fatal

# ---------- Field maps ----------

EXACT_MAP = {
    # Identity / header
    "Name": "NAME",
    "Aliases": "Aliases",
    "Motivations": "Motivations",
    "Languages": "Languages",
    "Ego Traits": "Ego Traits",
    "Faction": "Faction",
    "Interest": "Interest",
    "Gender": "Gender",
    "Sex": "Sex",
    "Age": "Age",
    "Muse": "Muse",
    "Background": "Background",
    "Career": "Career",

    # Aptitudes
    "Aptitudes.COG": "Cog",
    "Aptitudes.INT": "Int",
    "Aptitudes.REF": "Ref",
    "Aptitudes.SAV": "Sav",
    "Aptitudes.SOM": "Som",
    "Aptitudes.WIL": "Wil",

    # Derived stats
    "Derived Stats.Initiative": "Initiative",
    "Derived Stats.Lucidity": "Lucidity",
    "Derived Stats.Insanity Rating": "Insanity Rating",
    "Derived Stats.Stress Taken": "Stress Taken",
    "Derived Stats.Traumas Taken": "Traumas Taken",

    # Reputation
    "Reputation Scores.c-rep": "Rep C",
    "Reputation Scores.f-rep": "Rep F",
    "Reputation Scores.g-rep": "Rep G",
    "Reputation Scores.i-rep": "Rep I",
    "Reputation Scores.r-rep": "Rep R",
    "Reputation Scores.x-rep": "Rep X",
    # Autonomists — now prefers 'Rep AT'
    "Reputation Scores.@-rep": ("Rep AT", "Rep @", "Rep A"),

    # Morph / track
    "Morph": "MORPHmNAME",
    "Movement Rate": "Movement Rate",
    "Ware": "Ware",
    "Damage Taken": "DAMAGEmTAKEN",
    "Wounds Taken": "WOUNDSmTAKEN",
    "Wound Threshold": "WOUNDmTHRESHOLD",
    "Durability": "DURABILITY",
    "Death Rating": "DEATHmRATING",
    "Ego Flex": "EGOmFLEX",

    # Pools & misc
    "Flex": ("Flex", "FLEX"),
    "Starting Rez" : "UNSPENT REZ",

    # Secondary tracks
    "Insight": "Insight",
    "Moxie": "Moxie",
    "Vigor": "Vigor",

    # Base Active Skills
    "Focus Skills.Athletics": "Total Athletics",
    "Focus Skills.Deceive": "Total Deceive",
    "Focus Skills.Fray": "Total Fray",
    "Focus Skills.Free Fall": "Total Freefall",
    "Focus Skills.Guns": "Guns",
    "Focus Skills.Infiltrate": "Infiltrate",
    "Focus Skills.Infosec": "Infosec",
    "Focus Skills.Interface": "Interface",
    "Focus Skills.Kinesics": "Kinesics",
    "Focus Skills.Perceive": "Perceive",
    "Focus Skills.Persuade": "Persuade",
    "Focus Skills.Program": "Program",
    "Focus Skills.Provoke": "Provoke",
    "Focus Skills.PSI": "PSI",
    "Focus Skills.Research": "Research",
    "Focus Skills.Survival": "Survival",
    "Focus Skills.Melee": "Melee",
}

# Aptitude checks = aptitude * 3
CHECK_FIELDS = {
    "Aptitudes.COG": ("CogCheck",),
    "Aptitudes.INT": ("IntCheck",),
    "Aptitudes.REF": ("RefCheck",),
    "Aptitudes.SAV": ("SavCheck",),
    "Aptitudes.SOM": ("SomCheck",),
    "Aptitudes.WIL": ("WillCheck",),
}
