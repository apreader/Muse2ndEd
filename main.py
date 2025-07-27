import sys
import os
import random
from library_manager import LibraryManager

# Standard skill → aptitude mapping for base skill bonuses
# Keys here are prefixes to match skill names starting with these strings
SKILL_APTITUDE_MAP = {
    "Athletics": "SOM",
    "Deceive": "SAV",
    "Fray": "REF",
    "Free Fall": "SOM",
    "Guns": "REF",
    "Hardware": "COG",
    "Infosec": "COG",
    "Infiltrate": "REF",
    "Interface": "COG",
    "Kinesics": "SAV",
    "Medicine": "COG",
    "Melee": "SOM",
    "Perceive": "INT",
    "Persuade": "SAV",
    "Pilot": "REF",
    "Program": "COG",
    "Provoke": "SAV",
    "Psi": "WIL",
    "Research": "INT",
    "Survival": "INT",
}

def generate_aptitudes(morph_data):
    templates = {
        "Actioneer":  {"COG": 10, "INT": 15, "REF": 20, "SAV": 10, "SOM": 20, "WIL": 15},
        "Extrovert":  {"COG": 10, "INT": 20, "REF": 15, "SAV": 20, "SOM": 15, "WIL": 10},
        "Facilitator":{"COG": 15, "INT": 15, "REF": 10, "SAV": 20, "SOM": 10, "WIL": 20},
        "Factotum":   {"COG": 15, "INT": 15, "REF": 15, "SAV": 15, "SOM": 15, "WIL": 15},
        "Inquirer":   {"COG": 20, "INT": 20, "REF": 10, "SAV": 15, "SOM": 10, "WIL": 15},
        "Survivor":   {"COG": 15, "INT": 10, "REF": 15, "SAV": 10, "SOM": 20, "WIL": 20},
        "Thrill Seeker":{"COG": 20, "INT": 10, "REF": 20, "SAV": 15, "SOM": 15, "WIL": 10},
    }

    chosen_name = random.choice(list(templates.keys()))
    aptitudes = templates[chosen_name].copy()

    morph_bonus = morph_data.get("Bonus", {})
    if morph_bonus:
        apt = morph_bonus.get("Aptitude")
        amount = morph_bonus.get("Amount", 0)
        if apt in aptitudes:
            aptitudes[apt] = min(30, aptitudes[apt] + amount)

    for apt in aptitudes:
        aptitudes[apt] = max(5, min(30, aptitudes[apt]))

    return chosen_name, aptitudes


def select_languages(aptitudes):
    language_pool = [
        "Arabic", "Cantonese", "English", "French", "Hindi",
        "Japanese", "Mandarin", "Portuguese", "Russian", "Skandinavíska", "Spanish"
    ]

    known_languages = {"English"}
    known_languages.add(random.choice([lang for lang in language_pool if lang != "English"]))

    cog_int = aptitudes.get("COG", 0) + aptitudes.get("INT", 0)

    if cog_int >= 45:
        known_languages.update(random.sample(
            [lang for lang in language_pool if lang not in known_languages], 2
        ))
    elif cog_int >= 35:
        known_languages.add(random.choice(
            [lang for lang in language_pool if lang not in known_languages]
        ))

    return list(known_languages)


def combine_skills(background_skills, career_skills, interest_skills, faction_name):
    combined = {}

    # Add all skills from background, career, interest
    for skill_dict in (background_skills, career_skills, interest_skills):
        for skill, val in skill_dict.items():
            # Skip nested dicts for "Know": {"Choose One": 40} or similar
            if isinstance(val, dict):
                continue
            combined[skill] = combined.get(skill, 0) + val

    # Add faction knowledge: "Faction Knowledge" skill with 30 points
    knowledge_skill = f"Faction Knowledge: {faction_name}"
    combined[knowledge_skill] = 30

    # Cap skills at 80 and roll over points over 80 to next highest skill below 80
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


def add_aptitude_to_skills(skills, aptitudes):
    final_skills = skills.copy()

    for skill_name, apt in SKILL_APTITUDE_MAP.items():
        base_val = aptitudes.get(apt, 0)
        # Fray and Perceive have base values × 2
        if skill_name == "Fray" or skill_name == "Perceive":
            base_val *= 2

        # Find all skills that start with this skill_name prefix and add aptitude base
        for skill in final_skills.keys():
            if skill.startswith(skill_name):
                final_skills[skill] += base_val

        # If no matching skill found, add the skill with base aptitude value
        if not any(skill.startswith(skill_name) for skill in final_skills.keys()):
            final_skills[skill_name] = base_val

    # Cap all skills at 80 just in case
    for skill in final_skills:
        if final_skills[skill] > 80:
            final_skills[skill] = 80

    return final_skills


def save_character_to_file(character):
    folder = "characters"
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{character['Name']}.txt")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Name: {character['Name']}\n")
        f.write(f"Aliases: {', '.join(character['Aliases'])}\n")
        f.write(f"Motivations: {', '.join(character['Motivations'])}\n")
        f.write(f"Languages: {', '.join(character['Languages'])}\n")
        f.write(f"Ego Traits: {', '.join(character['Ego Traits'])}\n\n")

        f.write(f"Background: {character['Background']}\n")
        bg_data = character['Background Data']
        if bg_data.get("Description"):
            f.write(bg_data["Description"].strip() + "\n\n")
        if bg_data.get("Notes"):
            f.write(bg_data["Notes"].strip() + "\n\n")

        f.write(f"Career: {character['Career']}\n")
        f.write(f"Interest: {character['Interest']}\n")
        skills = character.get("Final Skills", {})
        if skills:
            f.write("Final Skills:\n")
            for skill, val in sorted(skills.items()):
                f.write(f"  {skill}: {val}\n")
            f.write("\n")

        f.write(f"Faction: {character['Faction']}\n")
        f.write(f"Gender: {character['Gender']}\n")
        f.write(f"Sex: {character['Sex']}\n")
        f.write(f"Age: {character['Age']}\n")
        f.write(f"Muse: {character['Muse']}\n\n")

        f.write(f"Morph: {character['Morph']} ({character['Morph Category']})\n")
        morph_data = character['Morph Data']
        if morph_data.get("Description"):
            f.write(morph_data["Description"].strip() + "\n\n")
        if morph_data.get("Notes"):
            f.write(morph_data["Notes"].strip() + "\n\n")

        f.write(f"Damage Taken: {character['Damage Taken']}\n")
        f.write(f"Wounds Taken: {character['Wounds Taken']}\n")
        f.write(f"Insight: {character['Insight']}\n")
        f.write(f"Moxie: {character['Moxie']}\n")
        f.write(f"Vigor: {character['Vigor']}\n")
        f.write(f"Flex: {character['Flex']}\n\n")

        f.write(f"Wound Threshold: {character['Wound Threshold']}\n")
        f.write(f"Durability: {character['Durability']}\n")
        f.write(f"Death Rating: {character['Death Rating']}\n")
        f.write(f"Ego Flex: {character['Ego Flex']}\n\n")

        f.write(f"Movement Rate: {character['Movement Rate']}\n")
        f.write(f"Ware: {', '.join(character['Ware'])}\n")
        f.write(f"Morph Traits: {', '.join(character['Morph Traits'])}\n")
        notes = character.get("Notes", "")
        if isinstance(notes, str):
            f.write(f"Notes:\n{notes.strip()}\n")

        f.write(f"{character['Aptitude Package']}\n")

        f.write("\nAptitudes:\n")
        for apt, val in character['Aptitudes'].items():
            f.write(f"  {apt}: {val}\n")

        f.write("\nDerived Stats:\n")
        for key, val in character['Derived Stats'].items():
            f.write(f"  {key}: {val}\n")

        f.write("\nReputation Scores:\n")
        for rep, score in character['Reputation'].items():
            f.write(f"  {rep}: {score}\n")


def generate_random_character(char_name, lm):
    sex = random.choices(["Male", "Female", "Intersex"], weights=[45, 45, 10])[0]
    morph_name, morph_category, morph_data = lm.get_random_morph()
    background_name, background_data = lm.get_random_background()
    gender, pronouns = lm.select_gender_and_pronouns()
    faction_name, faction_data = lm.get_random_entry("Factions")
    interest_name, interest_data = lm.get_random_interest()
    motivations = faction_data.get("Motivations", [])
    faction_motivation = f"+{faction_name} Interests"
    positives = [m for m in motivations if m.endswith("+") and m != faction_motivation]
    negatives = [m for m in motivations if m.endswith("-")]
    chosen_motivations = [faction_motivation]
    package_name, aptitudes = generate_aptitudes(morph_data)

    if positives:
        chosen_motivations.append(random.choice(positives))
    if negatives:
        chosen_motivations.append(random.choice(negatives))

    career_name, career_data = lm.get_random_career()

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

    combined_skills = combine_skills(background_skills, career_skills, interest_skills, faction_name)
    final_skills = add_aptitude_to_skills(combined_skills, aptitudes)

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
        "Aptitude Package": package_name,
        "Aptitudes": aptitudes,
        "Derived Stats": derived,
        "Final Skills": final_skills,
        "Reputation": {
            "@-REP": 10, "C-REP": 5, "F-REP": 0,
            "G-REP": 0, "I-REP": 0, "R-REP": 0, "X-REP": 0
        }
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <CharacterName>")
        return

    char_name = sys.argv[1]
    lm = LibraryManager()
    try:
        lm.load_all_libraries()
    except FileNotFoundError as e:
        print(f"Error loading libraries: {e}")
        return

    character = generate_random_character(char_name, lm)
    save_character_to_file(character)
    print(f"Character {char_name} saved successfully in characters/{char_name}.txt")


if __name__ == "__main__":
    main()
