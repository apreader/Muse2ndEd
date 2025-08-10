import os
import sys
from PyPDF2 import PdfReader, PdfWriter

# ------------------------------------------------------------
# Parse your plain-text character sheet into flat dict of key->value.
# Section headers end with ":" (e.g., "Aptitudes:"); entries inside
# a section become "Section.Key": "Value".
# ------------------------------------------------------------
def parse_character_txt(path):
    data = {}
    section = None
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.endswith(":") and ":" not in line[:-1]:
                section = line[:-1]
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if section:
                    data[f"{section}.{key}"] = value
                else:
                    data[key] = value
    return data

# ------------------------------------------------------------
# Best-effort mapping from your text keys -> PDF field names.
# Adjust any of these if your copy of the PDF uses different names.
# Only non-empty mappings are applied.
# ------------------------------------------------------------
SOURCE_TO_PDF = {
    # --- Identity / header ---
    "Name": "NAME",
    "Aliases": "Aliases",
    "Motivations": "Motivations",
    "Languages": "Languages",
    "Ego Traits": "Ego Traits",
    "Faction": "Faction",
    "Interest": "Interest",
    "Gender": "Gender",
    "Age": "Age",
    "Sex": "Sex",
    "Muse": "Muse",
    "Background": "Background",
    "Career": "Career",

    # --- Aptitudes ---
    "Aptitudes.COG": "Cog",
    "Aptitudes.INT": "Int",
    "Aptitudes.REF": "Ref",
    "Aptitudes.SAV": "Sav",
    "Aptitudes.SOM": "Som",
    "Aptitudes.WIL": "Wil",

    # --- Derived stats ---
    "Derived Stats.Initiative": "Initiative",
    "Derived Stats.Lucidity": "Lucidity",
    "Derived Stats.Trauma Threshold": "Trauma Threshold",
    "Derived Stats.Insanity Rating": "Insanity Rating",
    "Derived Stats.Stress Taken": "Stress Taken",
    "Derived Stats.Traumas Taken": "Traumas Taken",

    # --- Reputations ---
    "Reputation Scores.c-rep": "Rep C",
    "Reputation Scores.e-rep": "Rep E",
    "Reputation Scores.f-rep": "Rep F",
    "Reputation Scores.g-rep": "Rep G",
    "Reputation Scores.i-rep": "Rep I",
    "Reputation Scores.r-rep": "Rep R",
    "Reputation Scores.x-rep": "Rep X",

    # --- Morph / track ---
    "Morph": "MORPHmNAME",
    "Movement Rate": "Movement Rate",
    "Ware": "Ware",
    "Damage Taken": "DAMAGEmTAKEN",
    "Wounds Taken": "WOUNDSmTAKEN",
    "Wound Threshold": "WOUNDmTHRESHOLD",
    "Durability": "DURABILITY",
    "Death Rating": "DEATHmRATING",
    "Ego Flex": "EGOmFLEX",

    # Insight/Moxie/Vigor sometimes exist as separate fields too:
    "Insight": "Insight",
    "Moxie": "Moxie",
    "Vigor": "Vigor",

    # --- Base Active skills (Total <Skill> where applicable) ---
    "Focus Skills.Athletics": "Total Athletics",
    "Focus Skills.Deceive": "Total Deceive",
    "Focus Skills.Fray": "Total Fray",
    "Focus Skills.Free Fall": "Total Freefall",
    "Focus Skills.Guns": "Guns",
    "Focus Skills.Infiltrate": "Infiltrate",
    "Focus Skills.Infosec": "Infosec",
    "Focus Skills.Interface": "Interface",
    "Focus Skills.Kinesics": "Kinesics",
    "Focus Skills.Perceive": "Perceive",
    "Focus Skills.Persuade": "Persuade",
    "Focus Skills.Program": "Program",
    "Focus Skills.Provoke": "Provoke",
    "Focus Skills.PSI": "PSI",
    "Focus Skills.Research": "Research",
    "Focus Skills.Survival": "Survival",
    "Focus Skills.Melee": "Melee",
}

# ------------------------------------------------------------
# Attempt to auto-place grouped skills into numbered slots:
# - Hardware 1..5  (fields: "Hardware {i} Name", "Total Hardware {i}")
# - Pilot    1..5  (fields: "Pilot Name {i}", "Total Pilot {i}")
# - Medicine 1..4  (fields: "Medicine Name {i}", "Medicine {i}")
# - Exotic   1..2  (fields: "Exotic Skill {i} Name", "Total Exotic {i}")
# - Knowledge 1..6 (fields: "Know Name {i}", "Know Total {i}")
# You can tweak or disable this if you prefer manual mapping only.
# ------------------------------------------------------------
def auto_grouped_skill_fill(writer, page0, fields, src):
    # Collect each category
    hardware = []
    pilot = []
    medicine = []
    exotic = []
    know = []

    for k, v in src.items():
        if not k.startswith("Focus Skills."):
            continue
        label = k[len("Focus Skills."):]

        # Knowledge and Faction Knowledge
        if "Knowledge" in label:
            know.append((label, v))
            continue

        # Exotic Skill <something>
        if label.lower().startswith("exotic"):
            exotic.append((label, v))
            continue

        # Medicine or Medicine <specialty>
        if label.lower().startswith("medicine"):
            medicine.append((label, v))
            continue

        # Pilot (<vehicle>) or Pilot
        if label.lower().startswith("pilot"):
            pilot.append((label, v))
            continue

        # Hardware (<field>) or Hardware
        if label.lower().startswith("hardware"):
            hardware.append((label, v))
            continue

    # Fill helpers
    def set_field(name, val):
        # grace: attempt only if field name plausibly exists
        if name in fields:
            writer.update_page_form_field_values(page0, {name: val})

    # Hardware 1..5
    for i, (label, val) in enumerate(hardware[:5], start=1):
        set_field(f"Hardware {i} Name", label)
        set_field(f"Total Hardware {i}", val)

    # Pilot 1..5
    for i, (label, val) in enumerate(pilot[:5], start=1):
        set_field(f"Pilot Name {i}", label)
        set_field(f"Total Pilot {i}", val)

    # Medicine 1..4
    for i, (label, val) in enumerate(medicine[:4], start=1):
        set_field(f"Medicine Name {i}", label)
        set_field(f"Medicine {i}", val)

    # Exotic 1..2
    for i, (label, val) in enumerate(exotic[:2], start=1):
        set_field(f"Exotic Skill {i} Name", label)
        set_field(f"Total Exotic {i}", val)

    # Know 1..6
    for i, (label, val) in enumerate(know[:6], start=1):
        set_field(f"Know Name {i}", label)
        set_field(f"Know Total {i}", val)

# ------------------------------------------------------------
# Apply mapping and auto-grouped logic
# ------------------------------------------------------------
def fill_pdf_with_mapping(txt_path, pdf_path, output_path):
    src = parse_character_txt(txt_path)

    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    fields = reader.get_fields() or {}
    page0 = writer.pages[0]

    # 1) Direct mapped fields
    for src_key, pdf_field in SOURCE_TO_PDF.items():
        if not pdf_field:
            continue
        if src_key not in src:
            continue
        val = src[src_key]
        if pdf_field in fields:
            writer.update_page_form_field_values(page0, {pdf_field: val})

    # 2) Auto-place grouped skills if present
    auto_grouped_skill_fill(writer, page0, fields, src)

    # 3) Also try to fill any "Total <Skill>" base fields that exist but weren’t explicitly mapped above
    for k, v in src.items():
        if not k.startswith("Focus Skills."):
            continue
        label = k[len("Focus Skills."):].strip()
        candidate = f"Total {label}"
        if candidate in fields and candidate not in SOURCE_TO_PDF.values():
            writer.update_page_form_field_values(page0, {candidate: v})

    with open(output_path, "wb") as f:
        writer.write(f)
    print(f"✅ Saved: {output_path}")

# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 fill_ep2_character.py <character.txt>")
        sys.exit(1)

    txt_path = os.path.abspath(sys.argv[1])
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(script_dir, "EP2FormFill.pdf")
    if not os.path.exists(pdf_path):
        print(f"ERROR: EP2FormFill.pdf not found next to script: {pdf_path}")
        sys.exit(1)

    out_path = os.path.join(os.path.dirname(txt_path),
                            f"{os.path.splitext(os.path.basename(txt_path))[0]}_Filled.pdf")
    fill_pdf_with_mapping(txt_path, pdf_path, out_path)
