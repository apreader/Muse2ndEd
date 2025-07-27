import sys
import os
from library_manager import LibraryManager
from Character_Creator.generate_random_character import generate_random_character
from Character_Creator.save_character_to_file import save_character_to_file

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
    save_character_to_file(character, lm)

    print(f"Character '{char_name}' saved successfully in characters/{char_name}.txt")


if __name__ == "__main__":
    main()


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