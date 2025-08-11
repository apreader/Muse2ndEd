import os
import sys
from PyPDF2 import PdfReader, PdfWriter

# Allow both "python fill_ep2_character.py" and module mode
try:
    from .pdf_helpers import (
        parse_character_txt,
        format_know_label,
        enable_need_appearances,
        EXACT_MAP,
        CHECK_FIELDS,
        knowledge_apt_and_total,
    )
except ImportError:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    if SCRIPT_DIR not in sys.path:
        sys.path.insert(0, SCRIPT_DIR)
    from pdf_helpers import (
        parse_character_txt,
        format_know_label,
        enable_need_appearances,
        EXACT_MAP,
        CHECK_FIELDS,
        knowledge_apt_and_total,
    )

def fill_pdf_exact(txt_path, pdf_path, output_path, debug=False):
    src = parse_character_txt(txt_path, debug=debug)
    bg_desc = src.get("Background.Description")

    # Normalize Autonomist rep source key to the canonical '@-rep'
    for k in (
        "Reputation Scores.@-rep",
        "Reputation Scores.@rep",
        "Reputation Scores.a-rep",
        "Reputation Scores.arep",
        "Reputation Scores.A-Rep",
        "Reputation Scores.A Rep",
    ):
        if k in src:
            src["Reputation Scores.@-rep"] = src[k]
            break

    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    enable_need_appearances(writer, reader)

    fields = reader.get_fields() or {}
    page0 = writer.pages[0]

    if debug:
        keys = sorted(fields.keys())
        print(f"[DEBUG] Found {len(keys)} PDF fields in {os.path.basename(pdf_path)} (first 40 shown):")
        for i, n in enumerate(keys[:40], 1):
            print(f"  {i:2d}. {n}")
        print("")

    # ---- Exact mapping (supports tuples of candidate field names) ----
    missing_src = []
    missing_pdf = []

    for src_key, pdf_target in EXACT_MAP.items():
        if src_key not in src:
            missing_src.append(src_key)
            continue

        candidates = pdf_target if isinstance(pdf_target, (tuple, list)) else (pdf_target,)
        wrote = False
        for pdf_field in candidates:
            if pdf_field in fields:
                writer.update_page_form_field_values(page0, {pdf_field: src[src_key]})
                wrote = True
                break
        if not wrote:
            missing_pdf.append(candidates[0])

    # ---- Aptitude checks = aptitude * 3 ----
    def _to_int(s):
        try:
            return int(str(s).strip())
        except Exception:
            return None

    for src_key, pdf_checks in CHECK_FIELDS.items():
        apt = _to_int(src.get(src_key))
        if apt is None:
            continue
        check_val = str(apt * 3)
        for pdf_field in pdf_checks:
            if pdf_field in fields:
                writer.update_page_form_field_values(page0, {pdf_field: check_val})

    # ---- Background paragraph → Notes (if present) ----
    if bg_desc and "Notes" in fields:
        writer.update_page_form_field_values(page0, {"Notes": bg_desc})

    # ---- Grouped skills from Focus Skills.* ----
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

    # Knowledge 1..6 — NAME, APT, recalculated TOTAL
    if debug and know:
        print("[DEBUG] Knowledge labels going into PDF:")
        for i, (label, val) in enumerate(know[:6], 1):
            apt, tot = knowledge_apt_and_total(label, val, src)
            print(f"  {i}. '{label}' -> '{format_know_label(label)}' | Apt={apt} | Total={tot}")

    for i, (label, val) in enumerate(know[:6], start=1):
        apt, tot = knowledge_apt_and_total(label, val, src)
        set_field(f"Know Name {i}", format_know_label(label))
        set_field(f"Know Apt {i}", apt)
        set_field(f"Know Total {i}", tot)

    # ---- Write output ----
    with open(output_path, "wb") as f:
        writer.write(f)

    if missing_src:
        print("Note: these source keys weren't in the text (skipped):")
        for k in missing_src:
            print("  -", k)
    if missing_pdf:
        print("Note: these PDF fields weren't found (skipped):")
        for v in missing_pdf:
            print("  -", v)
    print(f"✅ Saved: {output_path}")

# ---------------------------
# CLI
# ---------------------------
def main():
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

    out_path = os.path.join(characters_dir, f"{char_name}_EP2.pdf")

    try:
        fill_pdf_exact(txt_path, pdf_path, out_path, debug=debug)
    except Exception as e:
        print("ERROR during fill:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
