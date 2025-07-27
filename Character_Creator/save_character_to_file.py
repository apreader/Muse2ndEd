import os

def save_character_to_file(character, library_manager):
    folder = "characters"
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, f"{character['Name']}.txt")

    # Fix Final Skills by selecting real choices for (Choose One) skills from background
    final_skills = character.get("Final Skills", {})
    background_name = character.get("Background")
    if library_manager and background_name:
        choice_skills = library_manager.get_choice_skills_for_background(background_name)
        if choice_skills:
            final_skills = library_manager.select_skills_from_choice(final_skills, choice_skills)

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
        if final_skills:
            f.write("Final Skills:\n")
            for skill, val in sorted(final_skills.items()):
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
        f.write(f"Insight: {sum(character['Insight'].values())}\n")
        f.write(f"Moxie: {sum(character['Moxie'].values())}\n")
        f.write(f"Vigor: {sum(character['Vigor'].values())}\n")

        f.write(f"Wound Threshold: {character['Wound Threshold']}\n")
        f.write(f"Durability: {character['Durability']}\n")
        f.write(f"Death Rating: {character['Death Rating']}\n")
        f.write(f"Ego Flex: {character['Ego Flex']}\n\n")

        f.write(f"Movement Rate: {character['Movement Rate']}\n")
        f.write(f"Ware: {', '.join(character['Ware'])}\n")
        
        if character['Morph Traits']:
            f.write(f"Morph Traits: {', '.join(character['Morph Traits'])}\n")

        notes = character.get("Notes", "")
        if isinstance(notes, str) and notes.strip():
            f.write(f"Notes:\n{notes.strip()}\n")

        f.write("\nAptitudes:\n")
        for apt, val in character['Aptitudes'].items():
            f.write(f"  {apt}: {val}\n")

        f.write("\nDerived Stats:\n")
        for key, val in character['Derived Stats'].items():
            f.write(f"  {key}: {val}\n")

        f.write("\nReputation Scores:\n")
        rep_data = character.get('Reputation', {})
        if isinstance(rep_data, dict):
            for rep, score in rep_data.items():
                f.write(f"  {rep}: {score}\n")
        else:
            f.write("  No reputation data available.\n")
