import random

def generate_aptitudes(morph_data):
    templates = {
        "Actioneer":  {"COG": 10, "INT": 15, "REF": 20, "SAV": 10, "SOM": 20, "WIL": 15},
        "Extrovert":  {"COG": 10, "INT": 20, "REF": 15, "SAV": 20, "SOM": 15, "WIL": 10},
        "Facilitator":{"COG": 15, "INT": 15, "REF": 10, "SAV": 20, "SOM": 10, "WIL": 20},
        "Factotum":   {"COG": 15, "INT": 15, "REF": 15, "SAV": 15, "SOM": 15, "WIL": 15},
        "Inquirer":   {"COG": 20, "INT": 20, "REF": 10, "SAV": 15, "SOM": 10, "WIL": 15},
        "Survivor":   {"COG": 15, "INT": 10, "REF": 15, "SAV": 10, "SOM": 20, "WIL": 20},
        "Thrill Seeker": {"COG": 20, "INT": 10, "REF": 20, "SAV": 15, "SOM": 15, "WIL": 10},
    }

    chosen_name = random.choice(list(templates.keys()))
    aptitudes = templates[chosen_name].copy()

    morph_bonus = morph_data.get("Bonus", {})
    if morph_bonus:
        apt = morph_bonus.get("Aptitude")
        amount = morph_bonus.get("Amount", 0)
        if apt in aptitudes:
            aptitudes[apt] = min(30, aptitudes[apt] + amount)

    for apt in aptitudes:
        aptitudes[apt] = max(5, min(30, aptitudes[apt]))

    return chosen_name, aptitudes
