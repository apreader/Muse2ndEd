import sys
import os
import subprocess
from library_manager import LibraryManager
from Character_Creator.generate_random_character import generate_random_character
from Character_Creator.save_character_to_file import save_character_to_file

def main():
    # --- simple arg parsing: <CharacterName> [--pdf] ---
    args = sys.argv[1:]
    if not args:
        print("Usage: python main.py <CharacterName> [--pdf]")
        return

    make_pdf = False
    names = []
    for a in args:
        if a == "--pdf":
            make_pdf = True
        else:
            names.append(a)

    if len(names) != 1:
        print("Usage: python main.py <CharacterName> [--pdf]")
        return

    char_name = names[0]

    lm = LibraryManager()
    try:
        lm.load_all_libraries()
    except FileNotFoundError as e:
        print(f"Error loading libraries: {e}")
        return

    character = generate_random_character(char_name, lm)
    save_character_to_file(character, lm)

    print(f"Character '{char_name}' saved successfully in characters/{char_name}.txt")

    if make_pdf:
        # fill_ep2_character.py lives at Character_Creator/pdf_conversion/fill_ep2_character.py
        repo_root = os.path.dirname(os.path.abspath(__file__))
        fill_script = os.path.join(repo_root, "Character_Creator", "pdf_conversion", "fill_ep2_character.py")
        if not os.path.exists(fill_script):
            print(f"ERROR: fill script not found at {fill_script}")
            return

        try:
            print(f"[pdf] Filling PDF for {char_name} …")
            # We taught the fill script to accept just the character name and find ../../characters/<name>.txt
            subprocess.run([sys.executable, fill_script, char_name], check=True)
            print(f"[pdf] Done. Wrote characters/{char_name}_Filled.pdf")
        except subprocess.CalledProcessError as e:
            print(f"[pdf] ERROR: PDF fill failed: {e}")

if __name__ == "__main__":
    main()
