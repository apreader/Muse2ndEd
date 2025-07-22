import json
import os
import re
import random

class LibraryManager:
    def __init__(self, library_folder="libraries"):
        self.library_folder = library_folder
        self.morphs = {}

    def load_morph_library_json(self, filename="Morph_Library.json"):
        filepath = os.path.join(self.library_folder, filename)
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"{filename} not found in {self.library_folder}")

        with open(filepath, "r", encoding="utf-8") as f:
            self.morphs = json.load(f)

        return self.morphs

    def parse_morphs_from_text(self, raw_text):
        morphs = {}

        morph_names = [
            "Flat", "Splicer", "Exalt", "Neotenic", "Ruster", "Bouncer", "Futura",
            "Hibernoid", "Menton", "Olympian", "Sylph", "Fury", "Ghost", "Remade"
        ]
        pattern = re.compile(r'^(?:' + '|'.join(morph_names) + r')$', re.MULTILINE)

        splits = pattern.split(raw_text)
        headers = pattern.findall(raw_text)

        for i, header in enumerate(headers):
            data_text = splits[i + 1]  # morph section text after header
            morphs[header] = self.extract_morph_data(data_text)

        return morphs

    def extract_morph_data(self, text):
        data = {}

        cost_avail_match = re.search(r'Cost:\s*(\d+)\s*MP\s*.\s*Avail:\s*(\d+)', text)

