from library_manager import LibraryManager
import json

def main():
    lm = LibraryManager()
    
    # Load morph library JSON from 'libraries/Morph_Library.json'
    try:
        lm.load_morph_library_json()
    except FileNotFoundError as e:
        print(e)
        return
    
    # Get a random morph
    try:
        morph_name, morph_data = lm.get_random_morph()
    except ValueError as e:
        print(e)
        return

    print(f"Randomly selected morph: {morph_name}")
    print(json.dumps(morph_data, indent=2))

    # Here you can extend: assign morph_data to a character sheet, etc.
    # For now, just a demonstration.

if __name__ == "__main__":
    main()
