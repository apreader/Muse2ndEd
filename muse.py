import random
import sys
import re

class Character:
    def __init__(self, name):
        self.name = name
        self.aptitudes = {
            "INT": 0, "REF": 0, "WIL": 0, "SOM": 0, "SAV": 0, "IN": 0, "CHA": 0
        }
        self.skills = {}
        self.background = None
        self.morph = None
        self.traits = []

    def choose_background(self, bg):
        self.background = bg
        for apt, val in bg.aptitudes.items():
            self.aptitudes[apt] = val
        for skill, val in bg.skills.items():
            self.skills[skill] = val
        self.traits = list(bg.traits)

    def assign_aptitudes(self):
        points = 30
        apt_names = list(self.aptitudes.keys())
        while points > 0:
            apt = random.choice(apt_names)
            self.aptitudes[apt] += 1
            points -= 1

    def buy_skills(self):
        skill_list = ["Hacking", "Stealth", "Persuasion", "Shooting"]
        points = 40
        while points > 0:
            skill = random.choice(skill_list)
            self.skills[skill] = self.skills.get(skill, 0) + 1
            points -= 1

    def select_morph(self, morph):
        self.morph = morph
        for apt, mod in morph.apt_modifiers.items():
            if apt in self.aptitudes:
                self.aptitudes[apt] += mod
        self.traits.extend(morph.traits)

    def __str__(self):
        return (
            f"Name: {self.name}\n"
            f"Background: {self.background.name if self.background else 'None'}\n"
            f"Morph: {self.morph.name if self.morph else 'None'}\n"
            f"Aptitudes:\n" + "\n".join(f"  {k}: {v}" for k, v in self.aptitudes.items()) + "\n"
            f"Skills:\n" + "\n".join(f"  {k}: {v}" for k, v in self.skills.items()) + "\n"
            f"Traits: {', '.join(self.traits) if self.traits else 'None'}\n"
        )

    def save_to_file(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(str(self))

def sanitize_filename(name):
    return re.sub(r'[^a-z0-9_-]', '', name.lower())

class Background:
    def __init__(self, name, aptitudes, skills, traits):
        self.name = name
        self.aptitudes = aptitudes
        self.skills = skills
        self.traits = traits

class Morph:
    def __init__(self, name, apt_modifiers, traits):
        self.name = name
        self.apt_modifiers = apt_modifiers
        self.traits = traits

# Main program
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python muse.py <character_name>")
        sys.exit(1)

    char_name = sys.argv[1]

    bg = Background("Ex-Scientist", {"INT": 4, "REF": 2, "WIL": 3}, {"Hacking": 3}, ["Curious"])
    morph = Morph("Infomorph", {"INT": +1, "REF": -1, "WIL": 0}, ["Datajack"])

    char = Character(char_name)
    char.choose_background(bg)
    char.assign_aptitudes()
    char.buy_skills()
    char.select_morph(morph)

    print(char)
    filename = f"{sanitize_filename(char.name)}_character.txt"
    char.save_to_file(filename)
    print(f"Character saved to {filename}")
