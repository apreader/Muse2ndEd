import sys
import os
from library_manager import LibraryManager
import random

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

    # Apply morph bonus (expect {"Aptitude": "COG", "Amount": 5} or similar)
    morph_bonus = morph_data.get("Bonus", {})
    if morph_bonus:
        apt = morph_bonus.get("Aptitude")
        amount = morph_bonus.get("Amount", 0)
        if apt in aptitudes:
            aptitudes[apt] = min(30, aptitudes[apt] + amount)

    # Clamp all aptitudes between 5 and 30 (mostly precaution)
    for apt in aptitudes:
        aptitudes[apt] = max(5, min(30, aptitudes[apt]))

    return chosen_name, aptitudes


def select_languages(aptitudes):
    language_pool = [
        "Arabic", "Cantonese", "English", "French", "Hindi",
        "Japanese", "Mandarin", "Portuguese", "Russian", "Skandinavíska", "Spanish"
    ]

    known_languages = set()
    known_languages.add("English")  # Default common language

    # Add a second base language
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


def save_character_to_file(character):
    folder = "characters"

    if not os.path.exists(folder):
        os.makedirs(folder)

    filename = f"{character['Name']}.txt"
    filepath = os.path.join(folder, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        # Basic info
        f.write(f"Name: {character.get('Name', '')}\n")
        f.write(f"Aliases: {', '.join(character.get('Aliases', []))}\n")
        f.write(f"Motivations: {', '.join(character.get('Motivations', []))}\n")
        f.write(f"Languages: {', '.join(character.get('Languages', []))}\n")
        f.write(f"Ego Traits: {', '.join(character.get('Ego Traits', []))}\n")

        f.write(f"\nBackground: {character.get('Background', '')}\n")
        bg_data = character.get('Background Data', {})
        if bg_data.get('Description'):
            f.write(bg_data['Description'].strip() + "\n\n")
        if bg_data.get('Notes'):
            f.write(bg_data['Notes'].strip() + "\n\n")

        f.write(f"Career: {character.get('Career', '')}\n")
        f.write(f"Interest: {character.get('Interest', '')}\n")
        f.write(f"Faction: {character.get('Faction', '')}\n")
        f.write(f"Gender: {character.get('Gender', '')}\n")
        f.write(f"Sex: {character.get('Sex', '')}\n")
        f.write(f"Age: {character.get('Age', '')}\n")
        f.write(f"Muse: {character.get('Muse', '')}\n")

        # Morph info
        f.write(f"\nMorph: {character.get('Morph', '')} ({character.get('Morph Category', '')})\n")
        morph_data = character.get('Morph Data', {})
        if morph_data.get('Description'):
            f.write(morph_data['Description'].strip() + "\n\n")
        if morph_data.get('Notes'):
            f.write(morph_data['Notes'].strip() + "\n\n")

        # Damage and Pools
        f.write(f"Damage Taken: {character.get('Damage Taken', 0)}\n")
        f.write(f"Wounds Taken: {character.get('Wounds Taken', 0)}\n")
        f.write(f"Insight: {character.get('Insight', {})}\n")
        f.write(f"Moxie: {character.get('Moxie', {})}\n")
        f.write(f"Vigor: {character.get('Vigor', {})}\n")
        f.write(f"Flex: {character.get('Flex', 0)}\n")

        # Thresholds and Ratings
        f.write(f"\nWound Threshold: {character.get('Wound Threshold', 0)}\n")
        f.write(f"Durability: {character.get('Durability', 0)}\n")
        f.write(f"Death Rating: {character.get('Death Rating', 0)}\n")
        f.write(f"Ego Flex: {character.get('Ego Flex', 0)}\n")

        f.write(f"\nMovement Rate: {character.get('Movement Rate', '')}\n")
        f.write(f"Ware: {', '.join(character.get('Ware', []))}\n")
        f.write(f"Morph Traits: {', '.join(character.get('Morph Traits', []))}\n")
        notes = character.get('Notes', '')
        if not isinstance(notes, str):
            notes = ''
        f.write(f"Notes:\n{notes.strip()}\n")

        # Aptitudes
        f.write("\nAptitudes:\n")
        for apt, val in character.get('Aptitudes', {}).items():
            f.write(f"  {apt}: {val}\n")

        # Derived stats
        f.write("\nDerived Stats:\n")
        for key, val in character.get('Derived Stats', {}).items():
            f.write(f"  {key}: {val}\n")

        # Active Skills
        f.write("\nActive Skills:\n")
        for skill in character.get('Active Skills', []):
            skill_name = skill.get("Skill", "???")
            apt = skill.get("Aptitude", "")
            typ = skill.get("Type", "")
            total = skill.get("Total", 0)
            extra = f" ({skill.get('Field', '')})" if "Field" in skill else ""
            f.write(f"  {skill_name}{extra:<20} APT: {apt:<5} TYPE: {typ:<10} TOTAL: {total}\n")

        # Reputation
        f.write("\nReputation Scores:\n")
        for rep, score in character.get('Reputation', {}).items():
            f.write(f"  {rep}: {score}\n")

def generate_random_character(char_name, lm):
    sex = random.choices(
        population=["Male", "Female", "Intersex"],
        weights=[45, 45, 10],
        k=1
    )[0]

    # Random morph and background
    morph_name, morph_category, morph_data = lm.get_random_morph()
    background_name, background_data = lm.get_random_background()
    gender, pronouns = lm.select_gender_and_pronouns()

    # Pick a faction at random from loaded factions
    faction_name, faction_data = lm.get_random_entry("Factions")

    # Faction-based motivation as "+[FactionName] Interests"
    faction_motivation = f"+{faction_name} Interests"

    # Extract motivations list
    motivations = faction_data.get("Motivations", [])

    # Separate positive and negative motivations
    positive_motivations = [m for m in motivations if m.endswith("+") and m != faction_motivation]
    negative_motivations = [m for m in motivations if m.endswith("-")]

    # Pick one positive and one negative motivation if available
    chosen_positive = random.choice(positive_motivations) if positive_motivations else None
    chosen_negative = random.choice(negative_motivations) if negative_motivations else None

    # Compose character motivations list
    character_motivations = [faction_motivation]
    if chosen_positive:
        character_motivations.append(chosen_positive)
    if chosen_negative:
        character_motivations.append(chosen_negative)

    # Random aptitudes
    template_name, aptitudes = generate_aptitudes(morph_data)



    # Derived stats (simplified)
    derived = {
        "Initiative": aptitudes["REF"] + aptitudes["INT"],
        "Lucidity": aptitudes["WIL"] * 2,
        "Trauma Threshold": aptitudes["WIL"] // 2,
        "Insanity Rating": aptitudes["WIL"] * 2,
        "Stress Taken": 0,
        "Traumas Taken": 0
    }

    # Pools (simplified)
    insight = {"COG": aptitudes["COG"], "INT": aptitudes["INT"]}
    moxie = {"SAV": aptitudes["SAV"], "WIL": aptitudes["WIL"], "REP": 0}
    vigor = {"REF": aptitudes["REF"], "SOM": aptitudes["SOM"]}

    # Example skills (abbreviated)
    skills = [
        {"Skill": "Fray", "Aptitude": "REFx2", "Type": "Combat", "Total": random.randint(30, 60)},
        {"Skill": "Guns", "Aptitude": "REF", "Type": "Combat", "Total": random.randint(40, 70)},
        {"Skill": "Infosec", "Aptitude": "COG", "Type": "Technical", "Total": random.randint(20, 60)},
        {"Skill": "Persuade", "Aptitude": "SAV", "Type": "Social", "Total": random.randint(30, 60)},
    ]

    return {
        "Name": char_name,
        "Aliases": [],
        "Motivations": character_motivations,
        "Languages": select_languages(aptitudes),
        "Ego Traits": ["Optimistic"],
        "Background": background_name,
        "Background Data": background_data,
        "Career": "Freelancer",
        "Interest": "Ancient Tech",
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
        "Active Skills": skills,
        "Reputation": {
            "@-REP": 10,
            "C-REP": 5,
            "F-REP": 0,
            "G-REP": 0,
            "I-REP": 0,
            "R-REP": 0,
            "X-REP": 0
        }
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <CharacterName>")
        return

    char_name = sys.argv[1]
    lm = LibraryManager()

    try:
        lm.load_morph_library_json()
        lm.load_background_library_json()
        lm.load_library("Factions", "Faction_Library.json")  # Make sure your faction JSON file is named exactly this
    except FileNotFoundError as e:
        print(e)
        return

    character = generate_random_character(char_name, lm)
    save_character_to_file(character)
    print(f"Character {char_name} saved successfully as characters/{char_name}.txt")

if __name__ == "__main__":
    main()
