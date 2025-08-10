import os
import sys
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject, BooleanObject

# ---------------------------
# Parse the plain-text sheet (fixed)
# ---------------------------
KNOWN_SECTIONS = {
    "Aptitudes",
    "Derived Stats",
    "Reputation Scores",
    "Focus Skills",
}
ALWAYS_TOP_LEVEL = {
    # Identity
    "Name", "Aliases", "Motivations", "Languages", "Ego Traits", "Faction",
    "Gender", "Sex", "Age", "Muse", "Career", "Interest",
    # Background + paragraph
    "Background",
    # Morph & tracks
    "Morph", "Movement Rate", "Ware",
    "Damage Taken", "Wounds Taken", "Insight", "Moxie", "Vigor",
    "Wound Threshold", "Durability", "Death Rating", "Ego Flex",
}

def parse_character_txt(path, debug=False):
    """
    - Only headers in KNOWN_SECTIONS open a section.
    - Keys in ALWAYS_TOP_LEVEL are always recorded at top level.
    - Captures Background description paragraph after 'Background:'.
    """
    data = {}
    section = None
    capture_bg = False
    bg_lines = []

    with open(path, "r", encoding="utf-8-sig") as f:
        lines = [ln.rstrip("\n") for ln in f]

    def flush_bg():
        nonlocal capture_bg, bg_lines
        if capture_bg and bg_lines:
            data["Background.Description"] = " ".join(s.strip() for s in bg_lines if s.strip())
        capture_bg = False
        bg_lines = []

    for raw in lines:
        s = raw.strip()

        # blank line: may end background paragraph
        if not s:
            flush_bg()
            continue

        # section header only if whitelisted
        if s.endswith(":") and ":" not in s[:-1]:
            flush_bg()
            header = s[:-1]
            if header in KNOWN_SECTIONS:
                section = header
            else:
                # treat as top-level empty key (e.g., 'Aliases:' with blank value)
                data[header] = ""
                section = None
                if header.lower() == "background":
                    capture_bg = True
                    bg_lines = []
            continue

        # key: value
        if ":" in raw:
            key, value = raw.rsplit(":", 1)
            key = key.strip()
            value = value.strip()

            # force certain keys to be top-level
            if key in ALWAYS_TOP_LEVEL:
                flush_bg()
                data[key] = value
                section = None
                if key.lower() == "background":
                    capture_bg = True
                    bg_lines = []
                continue

            # otherwise, inside a known section or top-level
            if section in KNOWN_SECTIONS:
                data[f"{section}.{key}"] = value
            else:
                data[key] = value

            # if we just wrote a top-level Background, begin capturing paragraph
            if section is None and key.lower() == "background":
                capture_bg = True
                bg_lines = []
            continue

        # paragraph text after Background:
        if capture_bg:
            bg_lines.append(raw)

    flush_bg()

    if debug:
        print(f"\n[DEBUG] Parsed {len(data)} keys from {os.path.basename(path)}:")
        for k in sorted(data.keys()):
            print(f"  - {k}: {data[k]}")
        print("")
    return data

# ---------------------------
# EXACT mapping (no fuzzy)
# ---------------------------
EXACT_MAP = {
    # Identity / header
    "Name": "NAME",
    "Aliases": "Aliases",
    "Motivations": "Motivations",
    "Languages": "Languages",
    "Ego Traits": "Ego Traits",
    "Faction": "Faction",
    "Interest": "Interest",
    "Gender": "Gender",
    "Sex": "Sex",
    "Age": "Age",
    "Muse": "Muse",
    "Background": "Background",
    "Career": "Career",

    # Aptitudes
    "Aptitudes.COG": "Cog",
    "Aptitudes.INT": "Int",
    "Aptitudes.REF": "Ref",
    "Aptitudes.SAV": "Sav",
    "Aptitudes.SOM": "Som",
    "Aptitudes.WIL": "Wil",

    # Derived stats
    "Derived Stats.Initiative": "Initiative",
    "Derived Stats.Lucidity": "Lucidity",
    "Derived Stats.Insanity Rating": "Insanity Rating",
    "Derived Stats.Stress Taken": "Stress Taken",
    "Derived Stats.Traumas Taken": "Traumas Taken",

    # Reputation (no Rep E if your template lacks it)
    "Reputation Scores.c-rep": "Rep C",
    "Reputation Scores.f-rep": "Rep F",
    "Reputation Scores.g-rep": "Rep G",
    "Reputation Scores.i-rep": "Rep I",
    "Reputation Scores.r-rep": "Rep R",
    "Reputation Scores.x-rep": "Rep X",

    # Morph / track
    "Morph": "MORPHmNAME",
    "Movement Rate": "Movement Rate",
    "Ware": "Ware",
    "Damage Taken": "DAMAGEmTAKEN",
    "Wounds Taken": "WOUNDSmTAKEN",
    "Wound Threshold": "WOUNDmTHRESHOLD",
    "Durability": "DURABILITY",
    "Death Rating": "DEATHmRATING",
    "Ego Flex": "EGOmFLEX",

    # Secondary tracks
    "Insight": "Insight",
    "Moxie": "Moxie",
    "Vigor": "Vigor",

    # Base Active Skills (exact PDF names)
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

# ---- formatter for Know names ----
import re
def format_know_label(label: str) -> str:
    m = re.match(r"\s*Faction\s*Knowledge\s*\((.+)\)\s*$", label, re.I)
    if m:
        return f"Faction: {m.group(1)}"
    m = re.match(r"\s*Knowledge\s*\((.+)\)\s*$", label, re.I)
    if m:
        return m.group(1)
    return label

def enable_need_appearances(writer: PdfWriter, reader: PdfReader):
    try:
        acro = reader.trailer["/Root"].get("/AcroForm")
        if acro is not None:
            writer._root_object.update({NameObject("/AcroForm"): acro})
            acro.update({NameObject("/NeedAppearances"): BooleanObject(True)})
    except Exception:
        pass  # non-fatal

def fill_pdf_exact(txt_path, pdf_path, output_path, debug=False):
    src = parse_character_txt(txt_path, debug=debug)
    bg_desc = src.get("Background.Description")

    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    enable_need_appearances(writer, reader)

    fields = reader.get_fields() or {}
    page0 = writer.pages[0]

    if debug:
        print(f"[DEBUG] Found {len(fields)} PDF fields in {os.path.basename(pdf_path)} (first 40 shown):")
        for i, n in enumerate(sorted(fields.keys())[:40], 1):
            print(f"  {i:2d}. {n}")
        print("")

    # 1) Apply exact mapping only
    missing_src = []
    missing_pdf = []
    for src_key, pdf_field in EXACT_MAP.items():
        if src_key not in src:
            missing_src.append(src_key)
            continue
        if pdf_field not in fields:
            missing_pdf.append(pdf_field)
            continue
        writer.update_page_form_field_values(page0, {pdf_field: src[src_key]})
        
# 2.5) Aptitude checks = aptitude * 3  (CogCheck/IntCheck/RefCheck/SavCheck/SomCheck/WillCheck)
    def to_int(s):
        try:
            return int(str(s).strip())
        except Exception:
            return None

    CHECK_FIELDS = {
        "Aptitudes.COG": ("CogCheck",),
        "Aptitudes.INT": ("IntCheck",),
        "Aptitudes.REF": ("RefCheck",),
        "Aptitudes.SAV": ("SavCheck",),
        "Aptitudes.SOM": ("SomCheck",),
        "Aptitudes.WIL": ("WillCheck",),  # your dump showed WillCheck existing
    }

    for src_key, pdf_checks in CHECK_FIELDS.items():
        apt = to_int(src.get(src_key))
        if apt is None:
            continue
        check_val = str(apt * 3)
        for pdf_field in pdf_checks:
            if pdf_field in fields:
                writer.update_page_form_field_values(page0, {pdf_field: check_val})


    # 2) Background paragraph to Notes (if present)
    if bg_desc and "Notes" in fields:
        writer.update_page_form_field_values(page0, {"Notes": bg_desc})

    # 3) Grouped skills — exact field names only
    hardware = []
    pilot = []
    medicine = []
    exotic = []
    know = []
    for k, v in src.items():
        if not k.startswith("Focus Skills."):
            continue
        label = k[len("Focus Skills."):].strip()
        l = label.lower()
        if "knowledge" in l:
            know.append((label, v))
        elif l.startswith("exotic"):
            exotic.append((label, v))
        elif l.startswith("medicine"):
            medicine.append((label, v))
        elif l.startswith("pilot"):
            pilot.append((label, v))
        elif l.startswith("hardware"):
            hardware.append((label, v))

    def set_field(name, val):
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

    # Knowledge 1..6 — write NAME (left) and numeric TOTAL (right)
    for i, (label, val) in enumerate(know[:6], start=1):
        set_field(f"Know Name {i}", format_know_label(label))
        set_field(f"Know Total {i}", val)

    with open(output_path, "wb") as f:
        writer.write(f)

    if missing_src:
        print("Note: these source keys weren't in the text (skipped):")
        for k in missing_src: print("  -", k)
    if missing_pdf:
        print("Note: these PDF fields weren't found (skipped):")
        for v in missing_pdf: print("  -", v)
    print(f"✅ Saved: {output_path}")

# ---------------------------
# CLI
# ---------------------------
if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("Usage:")
        print("  python3 fill_ep2_character.py <character_name> [--debug]")
        print("  python3 fill_ep2_character.py </full/or/relative/path/to/file.txt> [--debug]")
        sys.exit(1)

    arg = sys.argv[1]
    debug = (len(sys.argv) == 3 and sys.argv[2] == "--debug")

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Where the characters folder is relative to this script
    characters_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "characters"))
    os.makedirs(characters_dir, exist_ok=True)

    # Resolve txt_path:
    # - if user passed a .txt path, use it as-is
    # - otherwise, treat it as a character name inside characters_dir
    if arg.lower().endswith(".txt"):
        txt_path = os.path.abspath(arg)
        char_name = os.path.splitext(os.path.basename(txt_path))[0]
    else:
        char_name = arg
        txt_path = os.path.join(characters_dir, f"{char_name}.txt")

    if not os.path.exists(txt_path):
        print(f"ERROR: Character file not found: {txt_path}")
        sys.exit(1)

    # PDF template lives next to this script
    pdf_path = os.path.join(script_dir, "EP2FormFill.pdf")
    if not os.path.exists(pdf_path):
        print(f"ERROR: EP2FormFill.pdf not found next to script: {pdf_path}")
        sys.exit(1)

    # Always drop filled PDF in the characters folder
    out_path = os.path.join(characters_dir, f"{char_name}_EP2.pdf")

    try:
        fill_pdf_exact(txt_path, pdf_path, out_path, debug=debug)
    except Exception as e:
        print("ERROR during fill:", e)
        sys.exit(1)

