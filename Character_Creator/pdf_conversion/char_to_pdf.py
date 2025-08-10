import re
import sys
from PyPDF2 import PdfReader, PdfWriter

def parse_character_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    data = {}
    section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Section header (like Aptitudes:)
        if line.endswith(":") and not ":" in line[:-1]:
            section = line[:-1]
            continue

        # Key-value pair
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if section:
                data[f"{section}.{key}"] = value
            else:
                data[key] = value

    return data

def fill_pdf(form_pdf_path, txt_path, output_pdf_path):
    reader = PdfReader(form_pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    fields = reader.get_fields()
    data = parse_character_txt(txt_path)

    # Base field mapping
    field_map = {
        "NAME": data.get("Name"),
        "Aliases": data.get("Aliases"),
        "Motivations": data.get("Motivations"),
        "Languages": data.get("Languages"),
        "Ego Traits": data.get("Ego Traits"),
        "Faction": data.get("Faction"),
        "Gender": data.get("Gender"),
        "Sex": data.get("Sex"),
        "Age": data.get("Age"),
        "Muse": data.get("Muse"),
        "Career": data.get("Career"),
        "Interest": data.get("Interest"),
        "Background": data.get("Background"),

        "Cog": data.get("Aptitudes.COG"),
        "Int": data.get("Aptitudes.INT"),
        "Ref": data.get("Aptitudes.REF"),
        "Sav": data.get("Aptitudes.SAV"),
        "Som": data.get("Aptitudes.SOM"),
        "Wil": data.get("Aptitudes.WIL"),

        "Lucidity": data.get("Derived Stats.Lucidity"),
        "Initiative": data.get("Derived Stats.Initiative"),
        "Traumas Taken": data.get("Derived Stats.Traumas Taken"),
        "Stress Taken": data.get("Derived Stats.Stress Taken"),
        "Insanity Rating": data.get("Derived Stats.Insanity Rating"),

        "Rep C": data.get("Reputation Scores.c-rep"),
        "Rep E": data.get("Reputation Scores.e-rep"),
        "Rep F": data.get("Reputation Scores.f-rep"),
        "Rep G": data.get("Reputation Scores.g-rep"),
        "Rep I": data.get("Reputation Scores.i-rep"),
        "Rep R": data.get("Reputation Scores.r-rep"),
        "Rep X": data.get("Reputation Scores.x-rep"),

        "Movement Rate": data.get("Movement Rate"),
        "Ware": data.get("Ware"),
        "MORPHmNAME": data.get("Morph"),
        "DAMAGEmTAKEN": data.get("Damage Taken"),
        "WOUNDSmTAKEN": data.get("Wounds Taken"),
        "Insight": data.get("Insight"),
        "Moxie": data.get("Moxie"),
        "Vigor": data.get("Vigor"),
        "WOUNDmTHRESHOLD": data.get("Wound Threshold"),
        "DURABILITY": data.get("Durability"),
        "DEATHmRATING": data.get("Death Rating"),
        "EGOmFLEX": data.get("Ego Flex"),
    }

    for field, value in field_map.items():
        if field in fields and value is not None:
            writer.update_page_form_field_values(writer.pages[0], {field: value})

    # Base skills
    for key in data:
        if key.startswith("Focus Skills."):
            skill = key[len("Focus Skills."):].strip()
            base_field = f"Total {skill}"
            if base_field in fields:
                writer.update_page_form_field_values(writer.pages[0], {base_field: data[key]})

    # Know Skills (limit 6)
    know_index = 1
    for key in data:
        if key.startswith("Focus Skills.") and ("Knowledge" in key or "Faction Knowledge" in key):
            label = key[len("Focus Skills."):].strip()
            value = data[key]
            if know_index <= 6:
                writer.update_page_form_field_values(writer.pages[0], {
                    f"Know Name {know_index}": label,
                    f"Know Total {know_index}": value
                })
                know_index += 1

    # Grouped fields
    def fill_grouped(group_prefix, pdf_name_fmt, pdf_val_fmt, max_fields):
        count = 1
        for key in data:
            if key.startswith(f"Focus Skills.{group_prefix}"):
                name = key[len("Focus Skills."):].strip()
                value = data[key]
                if count <= max_fields:
                    writer.update_page_form_field_values(writer.pages[0], {
                        pdf_name_fmt.format(count): name,
                        pdf_val_fmt.format(count): value
                    })
                    count += 1

    fill_grouped("Hardware", "Hardware {} Name", "Total Hardware {}", 5)
    fill_grouped("Pilot", "Pilot Name {}", "Total Pilot {}", 5)
    fill_grouped("Medicine", "Medicine Name {}", "Medicine {}", 4)
    fill_grouped("Exotic", "Exotic Skill {} Name", "Total Exotic {}", 2)

    # Save result
    with open(output_pdf_path, "wb") as f:
        writer.write(f)

    print(f"PDF saved: {output_pdf_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python fill_ep2_character.py <form.pdf> <character.txt> <output.pdf>")
        sys.exit(1)

    fill_pdf(sys.argv[1], sys.argv[2], sys.argv[3])
