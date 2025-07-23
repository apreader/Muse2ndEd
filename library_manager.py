import json
import os
import random

class LibraryManager:
    def __init__(self, library_folder='libraries'):
        self.library_folder = library_folder
        self.libraries = {}  # e.g., {'Morphs': {...}, 'Gear': {...}}

    def load_background_library_json(self):
        self.load_library("Backgrounds", "Background_Library.json")


    def load_morph_library_json(self):
        # Loads the morph library from the expected JSON file
        self.load_library("Morphs", "Morph_Library.json")

    def get_random_morph(self):
        # Pick random category, then random morph from that category
        if "Morphs" not in self.libraries:
            raise ValueError("Morph library not loaded")
        morph_library = self.libraries["Morphs"]
        if not morph_library:
            raise ValueError("Morph library is empty")

        category = random.choice(list(morph_library.keys()))
        morphs = morph_library[category]
        if not morphs:
            raise ValueError(f"No morphs found in category '{category}'")
        morph_name = random.choice(list(morphs.keys()))
        morph_data = morphs[morph_name]
        return morph_name, category, morph_data

    # Get random background using RandomBackgroundRoll table
    def get_random_background(self):
        if "Backgrounds" not in self.libraries:
            raise ValueError("Background library not loaded")
        background_library = self.libraries["Backgrounds"]
        if not background_library:
            raise ValueError("Background library is empty")

        roll_table = background_library.get("RandomBackgroundRoll")
        if not roll_table:
            raise ValueError("RandomBackgroundRoll table missing in Background library")

        # Roll a d10 (1-10)
        roll = random.randint(1, 10)
        roll_str = str(roll)
        background_name = roll_table.get(roll_str)
        if not background_name:
            raise ValueError(f"No background found for roll {roll}")

        background_data = background_library.get(background_name)
        if not background_data:
            raise ValueError(f"Background data for '{background_name}' not found")

        return background_name, background_data


    # General-purpose loader

    def load_library(self, key_name, filename):
        """
        Loads a JSON file and stores it under a given key.
        Example: key_name = 'Morphs', filename = 'Morph_Library.json'
        """
        filepath = os.path.join(self.library_folder, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{filename} not found in {self.library_folder}")
        with open(filepath, 'r', encoding='utf-8') as f:
            self.libraries[key_name] = json.load(f)

    def get_random_entry(self, library_name):
        """
        Returns a (key, data) pair from a named library.
        """
        if library_name not in self.libraries:
            raise ValueError(f"Library '{library_name}' not loaded.")
        lib = self.libraries[library_name]
        if not lib:
            raise ValueError(f"Library '{library_name}' is empty.")
        key = random.choice(list(lib.keys()))
        return key, lib[key]

    def get_entry(self, library_name, key):
        """
        Returns a specific entry from a named library.
        """
        return self.libraries.get(library_name, {}).get(key, None)
