import os
import re

def save_character_to_file(character, lm=None):
    folder = "characters"
    if not os.path.exists(folder):
        os.makedirs(folder)

    filename = f"{character['Name']}.txt"
    filepath = os.path.join(folder, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        # Basic Info
        f.write(f"Name: {character.get('Name', '')}\n")
        f.write(f"Aliases: {', '.join(character.get('Aliases', []))}\n")
        f.write(f"Motivations: {', '.join(character.get('Motivations', []))}\n")
        f.write(f"Languages: {', '.join(character.get('Languages', []))}\n")
        f.write(f"Ego Traits: {', '.join(character.get('Ego Traits', []))}\n")
        f.write(f"Faction: {character.get('Faction', '')}\n")
        f.write(f"Gender: {character.get('Gender', '')}\n")
        f.write(f"Sex: {character.get('Sex', '')}\n")
        f.write(f"Age: {character.get('Age', '')}\n")
        f.write(f"Muse: {character.get('Muse', '')}\n")
        f.write(f"Career: {character.get('Career', '')}\n")
        f.write(f"Interest: {character.get('Interest', '')}\n")

        f.write(f"\nBackground: {character.get('Background', '')}\n")
        bg_data = character.get('Background Data', {})
        if bg_data.get("Description"):
            f.write(bg_data["Description"].strip() + "\n")

        # Aptitudes
        f.write("\nAptitudes:\n")
        for key, value in character.get("Aptitudes", {}).items():
            f.write(f"  {key}: {value}\n")

        # Derived Stats
        f.write("\nDerived Stats:\n")
        for key, value in character.get("Derived Stats", {}).items():
            f.write(f"  {key}: {value}\n")

        # Reputation
        f.write("\nReputation Scores:\n")
        for key, value in character.get("Reputation", {}).items():
            f.write(f"  {key}: {value}\n")

        # Skills
        f.write("\nFocus Skills:\n")
        for skill, rating in sorted(character.get("Final Skills", {}).items()):
            f.write(f"  {skill}: {rating}\n")

        # Morph
        f.write(f"\nMorph: {character.get('Morph', '')} ({character.get('Morph Category', '')})\n")
        if 'Notes' in character:
            notes = character['Notes']
            if isinstance(notes, list):
                notes = "\n".join(str(n).strip() for n in notes if n)
            else:
                notes = str(notes).strip()
            if notes:
                f.write(notes + "\n")

        f.write(f"Damage Taken: {character.get('Damage Taken', 0)}\n")
        f.write(f"Wounds Taken: {character.get('Wounds Taken', 0)}\n")

        insight = character.get("Insight", {})
        moxie = character.get("Moxie", {})
        vigor = character.get("Vigor", {})

        f.write(f"Insight: {sum(insight.values())}\n")
        f.write(f"Moxie: {sum(moxie.values())}\n")
        f.write(f"Vigor: {sum(vigor.values())}\n")

        f.write(f"Wound Threshold: {character.get('Wound Threshold', 0)}\n")
        f.write(f"Durability: {character.get('Durability', 0)}\n")
        f.write(f"Death Rating: {character.get('Death Rating', 0)}\n")
        f.write(f"Ego Flex: {character.get('Ego Flex', 1)}\n")

        f.write(f"\nMovement Rate: {character.get('Movement Rate', '')}\n")
        f.write("Ware: " + ", ".join(character.get("Ware", [])) + "\n")

        # Final Notes
        if notes:
            f.write("Notes:\n" + notes + "\n")
