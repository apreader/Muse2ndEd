import json
import re

def parse_morphs(raw_text):
    morphs = {}
    lines = raw_text.splitlines()

    current_morph = None
    current_data = {}

    # Regex patterns for fields
    cost_avail_re = re.compile(r'Cost:\s*(\d+)\s*MP\s*.\s*Avail:\s*(\d+)')
    wt_dur_dr_re = re.compile(r'WT:\s*(\d+)\s*.\s*DUR:\s*(\d+)\s*.\s*DR:\s*(\d+)')
    traits_re = re.compile(r'Insight\s*(\d+),\s*Moxie\s*(\d+),\s*Vigor\s*(\d+),\s*Flex\s*(\d+)')
    move_re = re.compile(r'Movement Rate:\s*(.+)')
    ware_re = re.compile(r'Ware:\s*(.+)')
    morph_traits_re = re.compile(r'Morph Traits:\s*(.+)')
    notes_re = re.compile(r'Notes:\s*(.+)')
    common_extras_re = re.compile(r'Common Extras:\s*(.+)')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect morph name lines: assume morph names have no colons and are capitalized words, often alone
        if (line.isalpha() or ' ' in line) and not ':' in line and line == line.title():
            # Save previous morph if any
            if current_morph:
                morphs[current_morph] = current_data
                current_data = {}
            current_morph = line
            continue

        if current_morph is None:
            # Skip any lines before first morph name
            continue

        # Parse lines with info
        m = cost_avail_re.search(line)
        if m:
            current_data['Cost'] = int(m.group(1))
            current_data['Avail'] = int(m.group(2))
            continue

        m = wt_dur_dr_re.search(line)
        if m:
            current_data['WT'] = int(m.group(1))
            current_data['DUR'] = int(m.group(2))
            current_data['DR'] = int(m.group(3))
            continue

        m = traits_re.search(line)
        if m:
            current_data['Insight'] = int(m.group(1))
            current_data['Moxie'] = int(m.group(2))
            current_data['Vigor'] = int(m.group(3))
            current_data['Flex'] = int(m.group(4))
            continue

        m = move_re.search(line)
        if m:
            current_data['Movement Rate'] = m.group(1)
            continue

        m = ware_re.search(line)
        if m:
            # Ware can be multiple items separated by commas
            current_data['Ware'] = [w.strip() for w in m.group(1).split(',')]
            continue

        m = morph_traits_re.search(line)
        if m:
            current_data['Morph Traits'] = m.group(1)
            continue

        m = notes_re.search(line)
        if m:
            current_data['Notes'] = m.group(1)
            continue

        m = common_extras_re.search(line)
        if m:
            current_data['Common Extras'] = m.group(1)
            continue

        # Could add more parsing here for other fields if needed

    # Save last morph
    if current_morph:
        morphs[current_morph] = current_data

    return morphs

def main():
    input_file = "libraries/Morph_Library.txt"
    output_file = "libraries/Morph_Library.json"

    with open(input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    morphs = parse_morphs(raw_text)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(morphs, f, indent=2)

    print(f"Converted {len(morphs)} morphs to JSON and saved to {output_file}")

if __name__ == "__main__":
    main()
