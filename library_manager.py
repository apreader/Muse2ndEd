import json
import os
import random

class LibraryManager:
    def __init__(self, library_folder='libraries'):
        self.library_folder = library_folder
        self.libraries = {
            "Morphs": {},
            "Backgrounds": {},
            "Factions": {},
            "Careers": {},
            "Genders": [],
            "Interests": {}
        }


    def load_all_libraries(self):
        self.load_library("Morphs", "Morph_Library.json")
        self.load_library("Backgrounds", "Background_Library.json")
        self.load_library("Factions", "Faction_Library.json")
        self.load_library("Careers", "Career_Library.json")
        self.load_gender_library()
        self.load_library("Interests", "Interest_Library.json")

    def load_library(self, key_name, filename):
        filepath = os.path.join(self.library_folder, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{filename} not found in {self.library_folder}")
        with open(filepath, 'r', encoding='utf-8') as f:
            self.libraries[key_name] = json.load(f)

    def load_gender_library(self):
        gender_file = os.path.join(self.library_folder, "Gender_Library.json")
        if not os.path.exists(gender_file):
            raise FileNotFoundError(f"Gender library file not found in {self.library_folder}")
        with open(gender_file, "r", encoding="utf-8") as f:
            self.libraries["Genders"] = json.load(f)

    def get_random_entry(self, library_name):
        if library_name not in self.libraries:
            raise ValueError(f"Library '{library_name}' not loaded.")
        lib = self.libraries[library_name]
        if not lib:
            raise ValueError(f"Library '{library_name}' is empty.")
        key = random.choice(list(lib.keys()))
        return key, lib[key]
    
    def get_random_interest(self):
        interests = self.libraries.get("Interests", {})
        if not interests:
            raise ValueError("Interests library is not loaded or empty.")

        random_interest_entry = interests.get("Random Interest")
        if not random_interest_entry:
            raise ValueError("Random Interest entry missing from Interests library")

        # Roll 1d10 to decide group
        roll = random.randint(1, 10)
        if roll <= 5:
            group_name = "Group 1"
        else:
            group_name = "Group 2"

        groups = random_interest_entry.get("Groups")
        if not groups or group_name not in groups:
            raise ValueError(f"Groups missing or {group_name} not found in Random Interest")

        group = groups[group_name]

        # For Group 2, handle "9-10" re-roll case
        while True:
            # Choose a random roll key from group keys
            keys = [k for k in group.keys() if k != "9-10"]
            chosen_roll = random.choice(keys)
            if chosen_roll == "9-10":
                # re-roll
                continue
            interest_name = group[chosen_roll]
            if interest_name not in interests:
                raise ValueError(f"Interest '{interest_name}' not found in Interests library")
            interest_data = interests[interest_name]
            return interest_name, interest_data

    def get_entry(self, library_name, key):
        return self.libraries.get(library_name, {}).get(key, None)

    def get_random_morph(self):
        morph_library = self.libraries.get("Morphs", {})
        if not morph_library:
            raise ValueError("Morph library is not loaded or empty.")
        category = random.choice(list(morph_library.keys()))
        morphs = morph_library[category]
        if not morphs:
            raise ValueError(f"No morphs found in category '{category}'")
        morph_name = random.choice(list(morphs.keys()))
        return morph_name, category, morphs[morph_name]

    def get_random_background(self):
        background_library = self.libraries.get("Backgrounds", {})
        if not background_library:
            raise ValueError("Background library is not loaded or empty.")
        roll_table = background_library.get("RandomBackgroundRoll")
        if not roll_table:
            raise ValueError("RandomBackgroundRoll table missing in Background library")
        roll = random.randint(1, 10)
        background_name = roll_table.get(str(roll))
        if not background_name:
            raise ValueError(f"No background found for roll {roll}")
        background_data = background_library.get(background_name)
        if not background_data:
            raise ValueError(f"Background data for '{background_name}' not found")
        return background_name, background_data

    def get_random_faction(self):
        factions = self.libraries.get("Factions", [])
        if not factions:
            raise ValueError("Factions library is not loaded or empty.")
        faction = random.choice(factions)
        return faction["Name"], faction

    def get_faction_by_name(self, name):
        factions = self.libraries.get("Factions", [])
        for faction in factions:
            if faction.get("Name") == name:
                return faction
        return None

    def get_random_career(self):
        careers = self.libraries.get("Careers", {})
        if not careers:
            raise ValueError("Careers library is not loaded or empty.")
        career_name = random.choice(list(careers.keys()))
        return career_name, careers[career_name]

    def get_career(self, career_name):
        return self.libraries.get("Careers", {}).get(career_name)

    def select_gender_and_pronouns(self):
        gender_list = self.libraries.get("Genders", [])
        weighted_main = ["Male", "Female", "Nonbinary"]
        alt_genders = [g for g in gender_list if g["name"] not in weighted_main]

        while True:
            roll = random.randint(1, 4)
            if roll <= 3:
                candidates = [g for g in gender_list if g["name"] in weighted_main]
                gender_entry = random.choice(candidates)
            else:
                gender_entry = random.choice(alt_genders)
                if gender_entry["name"] == "Two-Spirit" and random.randint(1, 4) != 4:
                    continue
            gender = gender_entry["name"]
            pronouns = random.choice(gender_entry["pronouns"])
            return gender, pronouns
