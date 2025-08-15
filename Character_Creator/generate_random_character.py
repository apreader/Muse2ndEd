import random

from .generate_aptitudes import generate_aptitudes
from .select_languages import select_languages
from .combine_skills import combine_skills
from .generate_reputation import generate_reputation
from library_manager import LibraryManager


# --- Minimal helpers (no behavior changes) -----------------------------------
def __ep2_norm(s):
    return (s or "").strip()

def __ep2_keynorm(s: str) -> str:
    """Aggressive, case-insensitive normalizer for fuzzy matches."""
    import re
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())

def __ep2_pick_profession_pack(career_name, lm: LibraryManager):
    """
    Find the canonical Profession pack name for the given career, using the actual
    structure of Gear_Pack_Library.json: { "Professions": { "<Career>": [items...] }, ... }.

    Returns the canonical key (e.g., "Mindhacker", "Techie"), or None if not found.
    """
    packs_root = getattr(lm, "get_library", lambda _n: None)("Gear_Pack_Library")
    if not career_name or not isinstance(packs_root, dict):
        return None

    profs = packs_root.get("Professions", {})
    if not isinstance(profs, dict) or not profs:
        return None

    # 1) Exact key match (case sensitive)
    if career_name in profs:
        return career_name

    # 2) Exact (case-insensitive)
    low = career_name.lower()
    for k in profs.keys():
        if k.lower() == low:
            return k

    # 3) Aggressive normalization equality
    needle = __ep2_keynorm(career_name)
    for k in profs.keys():
        if __ep2_keynorm(k) == needle:
            return k

    # 4) Substring/contains heuristic (both ways)
    for k in profs.keys():
        kn = __ep2_keynorm(k)
        if needle and (needle in kn or kn in needle):
            return k

    return None

def __ep2_choose_gear_packs(character: dict, lm: LibraryManager):
    """
    Choose Career/Profession pack names (names only — items are expanded elsewhere).
    Guarantees at least the Career pack if it exists in the JSON.
    """
    career = __ep2_norm(character.get("Career") or character.get("Profession"))
    chosen = []
    prof = __ep2_pick_profession_pack(career, lm)
    if prof:
        chosen.append(prof)

    # If somehow nothing matched (e.g., custom career), leave as empty list;
    # your postprocessor hook will still append Equipment from other sources.
    return chosen

def _harvest_structured_choices(*sources):
    """
    Pull structured choice blocks from career/interest dicts, e.g.:
      "Pilot Choices":   {"Points": 30, "Common Fields": ["Air","Ground","Nautical","Space"]}
      "Hardware Choices":{"Points": 40, "Common Fields": ["Aerospace","Electronics","Industrial"]}
      "Medicine Choices":{"Points": 20, "Common Fields": ["Biotech","Paramedic","Psychosurgery", ...]}
      "Know Choices":    [ {"Points": 60, "Common Fields": [...]}, {"Points": 30, "Common Fields": [...]} ]
    Returns list of {"SkillCategory","Rating","CommonFields"} like the background “ChoiceSkills”.
    """
    out = []
    mapping = {
        "Pilot Choices": "Pilot",
        "Hardware Choices": "Hardware",
        "Medicine Choices": "Medicine",
    }
    for src in sources:
        if not isinstance(src, dict):
            continue

        for key, category in mapping.items():
            block = src.get(key)
            if isinstance(block, dict):
                fields = block.get("Common Fields", [])
                points = block.get("Points", 0)
                if fields and points:
                    out.append({
                        "SkillCategory": category,
                        "Rating": int(points),
                        "CommonFields": [str(f).strip() for f in fields]
                    })

        klist = src.get("Know Choices")
        if isinstance(klist, list):
            for block in klist:
                if not isinstance(block, dict):
                    continue
                fields = block.get("Common Fields", [])
                points = block.get("Points", 0)
                if fields and points:
                    out.append({
                        "SkillCategory": "Know",
                        "Rating": int(points),
                        "CommonFields": [str(f).strip() for f in fields]
                    })
    return out
# -----------------------------------------------------------------------------


def generate_random_character(char_name, lm: LibraryManager):
    sex = random.choices(["Male", "Female", "Intersex"], weights=[45, 45, 10])[0]
    morph_name, morph_category, morph_data = lm.get_random_morph()
    background_name, background_data = lm.get_random_background()
    gender, pronouns = lm.select_gender_and_pronouns()
    faction_name, faction_data = lm.get_random_entry("Factions")
    interest_name, interest_data = lm.get_random_interest()
    career_name, career_data = lm.get_random_career()

    motivations = faction_data.get("Motivations", [])
    faction_motivation = f"+{faction_name} Interests"
    positives = [m for m in motivations if m.endswith("+") and m != faction_motivation]
    negatives = [m for m in motivations if m.endswith("-")]
    chosen_motivations = [faction_motivation]
    if positives:
        chosen_motivations.append(random.choice(positives))
    if negatives:
        chosen_motivations.append(random.choice(negatives))

    package_name, aptitudes = generate_aptitudes(morph_data)

    derived = {
        "Initiative": aptitudes["REF"] + aptitudes["INT"],
        "Lucidity": aptitudes["WIL"] * 2,
        "Trauma Threshold": aptitudes["WIL"] // 2,
        "Insanity Rating": aptitudes["WIL"] * 2,
        "Stress Taken": 0,
        "Traumas Taken": 0,
    }

    insight = {"COG": aptitudes["COG"], "INT": aptitudes["INT"]}
    moxie = {"SAV": aptitudes["SAV"], "WIL": aptitudes["WIL"], "REP": 0}
    vigor = {"REF": aptitudes["REF"], "SOM": aptitudes["SOM"]}

    # 1) Use pre-parsed background choice skills (added by LibraryManager)
    choice_skills = background_data.get("ChoiceSkills", [])

    # 2) Harvest structured choices from Career and Interest
    choice_skills += _harvest_structured_choices(career_data, interest_data)

    # 3) Ask LM to pick a field for each choice
    chosen_fields = lm.pick_choice_skill_fields(choice_skills)

    background_skills = background_data.get("Skills", {})
    career_skills = career_data.get("Skills", {})
    interest_skills = interest_data.get("Skills", {})

    final_skills = combine_skills(
        lm,
        background_skills,
        career_skills,
        interest_skills,
        faction_name,
        aptitudes,
        chosen_fields
    )

    reputation = generate_reputation(
        faction=faction_name,
        background=background_name,
        career=career_name,
        interests=interest_name,
        is_uplift=(morph_category.lower() == "uplift")
    )

    # Build the character dict
    character = {
        "Name": char_name,
        "Aliases": [],
        "Motivations": chosen_motivations,
        "Languages": select_languages(aptitudes),
        "Ego Traits": ["Optimistic"],
        "Background": background_name,
        "Background Data": background_data,
        "Career": career_name,
        "Career Data": career_data,
        "Interest": interest_name,
        "Interest Data": interest_data,
        "Faction": faction_name,
        "Gender": f"{gender} ({pronouns})",
        "Sex": sex,
        "Age": "35",
        "Muse": "Kira",
        "Morph": morph_name,
        "Morph Category": morph_category,
        "Morph Data": morph_data,
        "Damage Taken": 0,
        "Wounds Taken": 0,
        "Insight": insight,
        "Moxie": moxie,
        "Vigor": vigor,
        # Flex is set below (default 1); keep Ego Flex separate if you use both
        "Wound Threshold": 6,
        "Durability": morph_data.get("DUR", 30),
        "Death Rating": morph_data.get("DR", 45),
        "Ego Flex": 1,
        "Movement Rate": morph_data.get("Movement Rate", "Walker 4/20"),
        "Ware": morph_data.get("Ware", []),
        "Morph Traits": morph_data.get("Traits", []),
        "Notes": morph_data.get("Notes", ""),
        "Aptitudes": aptitudes,
        "Derived Stats": derived,
        "Final Skills": final_skills,
        "Reputation": reputation,
        # "Starting Rez" and "Gear Packs" added below
    }

    # --- Steps 1–3 (non-destructive) -----------------------------------------
    # 1) Flex rating (default 1 if not already set upstream)
    try:
        character["Flex"] = max(0, int(character.get("Flex", 1)))
    except Exception:
        character["Flex"] = 1

    # 2) Starting Rez
    character["Starting Rez"] = 15

    # 3) Gear Packs (names only; do not overwrite if already set)
    if not character.get("Gear Packs"):
        try:
            packs = __ep2_choose_gear_packs(character, lm)
            # Always ensure at least the Career pack is included if available
            character["Gear Packs"] = packs if isinstance(packs, list) else []
        except Exception:
            character["Gear Packs"] = character.get("Gear Packs", [])
    # -------------------------------------------------------------------------

    return character
