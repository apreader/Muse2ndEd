import os

def _flatten_reputation_for_pdf(character):
    """
    Ensure top-level PDF field names like 'Reputation Scores.c-rep' exist.
    Also normalize common aliases so '@-rep' is always present.
    """
    rep = character.get("Reputation", {}) or {}

    # Normalize aliases to canonical '@-rep' if it's missing
    if "@-rep" not in rep:
        for alias in ("@rep", "a-rep", "arep", "A-Rep", "A Rep", "e-rep"):
            if alias in rep:
                rep["@-rep"] = rep[alias]
                break

    # Emit canonical keys expected by the PDF filler
    for key in ["c-rep", "f-rep", "g-rep", "i-rep", "r-rep", "x-rep", "@-rep"]:
        character[f"Reputation Scores.{key}"] = int(rep.get(key, 0))


def save_character_to_file(character, lm=None):
    # Make sure PDF filler can find the expected reputation fields
    _flatten_reputation_for_pdf(character)

    folder = "characters"
    if not os.path.exists(folder):
        os.makedirs(folder)

    filename = f"{character['Name']}.txt"
    filepath = os.path.join(folder, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        # Basic Info
        f.write(f"Name: {character.get('Name', '')}\n")
        f.write(f"Aliases: {', '.join(character.get('Aliases', []))}\n")
        f.write(f"Motivations: {', '.join(character.get('Motivations', []))}\n")
        f.write(f"Languages: {', '.join(character.get('Languages', []))}\n")
        f.write(f"Ego Traits: {', '.join(character.get('Ego Traits', []))}\n")
        f.write(f"Faction: {character.get('Faction', '')}\n")
        f.write(f"Gender: {character.get('Gender', '')}\n")
        f.write(f"Sex: {character.get('Sex', '')}\n")
        f.write(f"Age: {character.get('Age', '')}\n")
        f.write(f"Muse: {character.get('Muse', '')}\n")
        f.write(f"Career: {character.get('Career', '')}\n")
        f.write(f"Interest: {character.get('Interest', '')}\n")

        f.write(f"\nBackground: {character.get('Background', '')}\n")
        bg_data = character.get('Background Data', {})
        if bg_data.get("Description"):
            f.write(bg_data["Description"].strip() + "\n")

        # Aptitudes
        f.write("\nAptitudes:\n")
        for key, value in character.get("Aptitudes", {}).items():
            f.write(f"  {key}: {value}\n")

        # Derived Stats
        f.write("\nDerived Stats:\n")
        for key, value in character.get("Derived Stats", {}).items():
            f.write(f"  {key}: {value}\n")

        # Reputation (normalized + canonical order)
        f.write("\nReputation Scores:\n")
        rep_src = dict(character.get("Reputation", {}) or {})

        # Normalize aliases so the TXT always has '@-rep'
        if "@-rep" not in rep_src:
            for alias in ("@rep", "a-rep", "arep", "A-Rep", "A Rep", "e-rep"):
                if alias in rep_src:
                    rep_src["@-rep"] = rep_src[alias]
                    break

        for key in ["c-rep", "f-rep", "g-rep", "i-rep", "r-rep", "x-rep", "@-rep"]:
            f.write(f"  {key}: {int(rep_src.get(key, 0))}\n")

        # Skills
        f.write("\nFocus Skills:\n")
        for skill, rating in sorted(character.get("Final Skills", {}).items()):
            f.write(f"  {skill}: {rating}\n")

        # Morph
        f.write(f"\nMorph: {character.get('Morph', '')} ({character.get('Morph Category', '')})\n")

        # Collect notes text (write once at the end)
        notes = ""
        if 'Notes' in character:
            raw_notes = character['Notes']
            if isinstance(raw_notes, list):
                notes = "\n".join(str(n).strip() for n in raw_notes if n)
            else:
                notes = str(raw_notes).strip()

        f.write(f"Damage Taken: {character.get('Damage Taken', 0)}\n")
        f.write(f"Wounds Taken: {character.get('Wounds Taken', 0)}\n")

        insight = character.get("Insight", {})
        moxie = character.get("Moxie", {})
        vigor = character.get("Vigor", {})

        f.write(f"Insight: {sum(insight.values())}\n")
        f.write(f"Moxie: {sum(moxie.values())}\n")
        f.write(f"Vigor: {sum(vigor.values())}\n")

        f.write(f"Wound Threshold: {character.get('Wound Threshold', 0)}\n")
        f.write(f"Durability: {character.get('Durability', 0)}\n")
        f.write(f"Death Rating: {character.get('Death Rating', 0)}\n")
        f.write(f"Ego Flex: {character.get('Ego Flex', 1)}\n")

        f.write(f"\nMovement Rate: {character.get('Movement Rate', '')}\n")
        f.write("Ware: " + ", ".join(character.get("Ware", [])) + "\n")

        # --- EP2 TXT additions: Steps 1–3 ---
        # Flex and Starting Rez
        f.write(f"\nFlex: {character.get('Flex', 1)}\n")
        f.write(f"Starting Rez: {character.get('Starting Rez', 15)}\n")

        # Gear Packs (names only; print [None] if empty)
        packs = character.get("Gear Packs") or []
        f.write("\nGear Packs:\n")
        if packs:
            for p in packs:
                f.write(f"  - {p}\n")
        else:
            f.write("  [None]\n")
        # --- end EP2 TXT additions ---

        # Final Notes (single place to print notes)
        if notes:
            f.write("\nNotes:\n" + notes + "\n")
