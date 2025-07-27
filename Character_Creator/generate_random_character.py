from .generate_aptitudes import generate_aptitudes
from .select_languages import select_languages
from .combine_skills import combine_skills
from .save_character_to_file import save_character_to_file
from library_manager import LibraryManager
from .generate_reputation import generate_reputation
import random

def generate_random_character(char_name, lm):
    # (existing code...)
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
        "Traumas Taken": 0
    }

    insight = {"COG": aptitudes["COG"], "INT": aptitudes["INT"]}
    moxie = {"SAV": aptitudes["SAV"], "WIL": aptitudes["WIL"], "REP": 0}
    vigor = {"REF": aptitudes["REF"], "SOM": aptitudes["SOM"]}

    background_skills = background_data.get("Skills", {})
    career_skills = career_data.get("Skills", {})
    interest_skills = interest_data.get("Skills", {})

    # Combine all raw skills first
    raw_skills = combine_skills(background_skills, career_skills, interest_skills, faction_name, aptitudes)

    # Process choice skills from background
    choice_skills = background_data.get("ChoiceSkills", [])

    final_skills = {}

    # Helper: for each skill key, if it is a choice skill, pick a field randomly and rename
    def process_skill_name(skill_name, rating):
        # Check if skill_name is one of the choice categories, e.g. "Know: (Choose One)" or "Hardware: (Choose One)"
        # We'll match base category ignoring case and colons/spaces.
        # We'll map "Know" to "Knowledge" and format properly.
        for choice in choice_skills:
            base_cat = choice["SkillCategory"]  # e.g. "Know", "Hardware", "Medicine"
            if skill_name.startswith(f"{base_cat}: (Choose One)"):
                # Pick a random field from CommonFields
                field = random.choice(choice["CommonFields"])
                # Format skill name properly
                display_cat = base_cat
                if base_cat.lower() == "know":
                    display_cat = "Knowledge"
                # Compose skill name as: Knowledge (field)
                return f"{display_cat} ({field})", choice["Rating"]
            # Also support when skill_name matches exactly the base_cat without (Choose One)
            elif skill_name.startswith(f"{base_cat}:"):
                # e.g. "Know: Rep Nets"
                if base_cat.lower() == "know":
                    display_cat = "Knowledge"
                else:
                    display_cat = base_cat
                # Remove colon, keep field as is after colon
                field = skill_name[len(base_cat)+1:].strip()
                return f"{display_cat} ({field})", rating
        # If no match, return skill as is
        return skill_name, rating

    # Process all raw skills, replacing choice skills properly and avoiding duplicates
    for skill_name, rating in raw_skills.items():
        # Replace skill name if needed
        new_name, new_rating = process_skill_name(skill_name, rating)

        # If skill already in final_skills, keep the highest rating
        if new_name in final_skills:
            if new_rating > final_skills[new_name]:
                final_skills[new_name] = new_rating
        else:
            final_skills[new_name] = new_rating

    # Now, for any choice skills NOT explicitly in raw_skills, add one choice skill per category
    # This ensures at least one chosen skill per choice category
    for choice in choice_skills:
        base_cat = choice["SkillCategory"]
        # Check if already present in final_skills (any skill starting with base_cat)
        already_present = any(s.startswith(base_cat) or s.startswith("Knowledge") for s in final_skills.keys())
        if not already_present:
            field = random.choice(choice["CommonFields"])
            display_cat = base_cat
            if base_cat.lower() == "know":
                display_cat = "Knowledge"
            skill_key = f"{display_cat} ({field})"
            rating = choice["Rating"]
            if skill_key not in final_skills:
                final_skills[skill_key] = rating

    reputation = generate_reputation(
        faction=faction_name,
        background=background_name,
        career=career_name,
        interests=interest_name,
        is_uplift=(morph_category.lower() == "uplift")
    )

    return {
        "Name": char_name,
        "Aliases": [],
        "Motivations": chosen_motivations,
        "Languages": select_languages(aptitudes),
        "Ego Traits": ["Optimistic"],
        "Background": background_name,
        "Background Data": background_data,
        "Career": career_name,
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
        "Flex": 1,
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
        "Reputation": reputation
    }
