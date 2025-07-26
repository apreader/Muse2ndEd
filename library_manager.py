import json
import os
import random

class LibraryManager:
    def __init__(self, library_folder='libraries'):
        self.library_folder = library_folder
        self.libraries = {}

    def load_gender_library(self):
        gender_file = os.path.join(self.library_folder, "Gender_Library.json")
        with open(gender_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_background_library_json(self):
        self.load_library("Backgrounds", "Background_Library.json")

    def load_morph_library_json(self):
        self.load_library("Morphs", "Morph_Library.json")
    
    def load_faction_library_json(self):
        filename = "Faction_Library.json"
        self.load_library("Factions", filename)

    def get_random_faction(self):
        if "Factions" not in self.libraries:
            raise ValueError("Factions library not loaded")
        factions = self.libraries["Factions"]
        if not factions:
            raise ValueError("Factions library is empty")
        faction = random.choice(factions)
        return faction["Name"], faction

    def get_faction_by_name(self, name):
        if "Factions" not in self.libraries:
            raise ValueError("Factions library not loaded")
        for faction in self.libraries["Factions"]:
            if faction.get("Name") == name:
                return faction
        return None

    def get_random_morph(self):
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

    def get_random_background(self):
        if "Backgrounds" not in self.libraries:
            raise ValueError("Background library not loaded")
        background_library = self.libraries["Backgrounds"]
        if not background_library:
            raise ValueError("Background library is empty")

        roll_table = background_library.get("RandomBackgroundRoll")
        if not roll_table:
            raise ValueError("RandomBackgroundRoll table missing in Background library")

        roll = random.randint(1, 10)
        roll_str = str(roll)
        background_name = roll_table.get(roll_str)
        if not background_name:
            raise ValueError(f"No background found for roll {roll}")

        background_data = background_library.get(background_name)
        if not background_data:
            raise ValueError(f"Background data for '{background_name}' not found")

        return background_name, background_data

    def select_gender_and_pronouns(self):
        gender_list = self.load_gender_library()  # this returns a list of dicts
    
        weighted_main = ["Male", "Female", "Nonbinary"]
        alt_genders = [g for g in gender_list if g["name"] not in weighted_main]

        while True:
            roll = random.randint(1, 4)
            if roll <= 3:
                # Pick from weighted main genders
                candidates = [g for g in gender_list if g["name"] in weighted_main]
                gender_entry = random.choice(candidates)
            else:
                # Pick from alternative genders
                gender_entry = random.choice(alt_genders)
                if gender_entry["name"] == "Two-Spirit":
                    # reroll unless hit again
                    if random.randint(1, 4) != 4:
                        continue

            gender = gender_entry["name"]
            pronouns = random.choice(gender_entry["pronouns"])
            return gender, pronouns

    def load_library(self, key_name, filename):
        filepath = os.path.join(self.library_folder, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{filename} not found in {self.library_folder}")
        with open(filepath, 'r', encoding='utf-8') as f:
            self.libraries[key_name] = json.load(f)

    def get_random_entry(self, library_name):
        if library_name not in self.libraries:
            raise ValueError(f"Library '{library_name}' not loaded.")
        lib = self.libraries[library_name]
        if not lib:
            raise ValueError(f"Library '{library_name}' is empty.")
        key = random.choice(list(lib.keys()))
        return key, lib[key]

    def get_entry(self, library_name, key):
        return self.libraries.get(library_name, {}).get(key, None)
