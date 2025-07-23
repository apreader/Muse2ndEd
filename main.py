import sys
import os
from library_manager import LibraryManager

def save_character_to_file(character):
    folder = "characters"
    if not os.path.exists(folder):
        os.makedirs(folder)

    filename = f"{character['Name']}.txt"
    filepath = os.path.join(folder, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Name: {character.get('Name', '')}\n")

        # Write full background description and notes with spacing
        background_name = character.get('Background', '')
        background_data = character.get('Background Data', {})
        description = background_data.get("Description", "")
        notes = background_data.get("Notes", "")

        f.write(f"Background: {background_name}\n")
        if description:
            f.write(description.strip() + "\n\n")
        if notes:
            f.write(notes.strip() + "\n\n")


        # Morph name with category in parentheses
        morph_name = character.get('Morph', '')
        morph_category = character.get('Morph Category', '')
        if morph_name and morph_category:
            f.write(f"Morph: {morph_name} ({morph_category.rstrip('s')})\n")
        else:
            f.write(f"Morph: {morph_name}\n")

        # Write morph description and notes, if any
        morph_data = character.get('Morph Data', {})
        description = morph_data.get("Description", "")
        notes = morph_data.get("Notes", "")

        if description:
            f.write(description.strip() + "\n\n")
        if notes:
            f.write(notes.strip() + "\n\n")

        # Write other morph fields, excluding Description and Notes
        for key, value in morph_data.items():
            if key in ("Description", "Notes"):
                continue
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            f.write(f"{key}: {value}\n")


        # Aptitudes
        f.write("\nAptitudes:\n")
        aptitudes = character.get('Aptitudes', {})
        for key, value in aptitudes.items():
            f.write(f"  {key}: {value}\n")

        # Skills
        f.write("\nSkills:\n")
        skills = character.get('Skills', {})
        for key, value in skills.items():
            f.write(f"  {key}: {value}\n")

        # Traits
        traits = character.get('Traits', [])
        if isinstance(traits, list):
            traits = ', '.join(traits)
        f.write(f"\nTraits: {traits}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <CharacterName>")
        return

    char_name = sys.argv[1]

    lm = LibraryManager()

    # Load libraries
    try:
        lm.load_morph_library_json()
        lm.load_background_library_json()
    except FileNotFoundError as e:
        print(e)
        return

    # Get random morph
    try:
        morph_name, morph_category, morph_data = lm.get_random_morph()
    except ValueError as e:
        print(e)
        return

    # Get random background
    try:
        background_name, background_data = lm.get_random_background()
    except ValueError as e:
        print(e)
        return

    # Assemble character dictionary
    character = {
        "Name": char_name,
        "Background": background_name,
        "Background Data": background_data,
        "Morph": morph_name,
        "Morph Category": morph_category,
        "Morph Data": morph_data,
        "Aptitudes": {
            "INT": 7, "REF": 8, "WIL": 5, "SOM": 5, "SAV": 5, "IN": 4, "CHA": 5
        },
        "Skills": {
            "Hacking": 13, "Shooting": 16, "Persuasion": 9, "Stealth": 5
        },
        "Traits": ["Curious", "Datajack"]
    }

    save_character_to_file(character)
    print(f"Character {char_name} saved successfully as characters/{char_name}.txt")

if __name__ == "__main__":
    main()
