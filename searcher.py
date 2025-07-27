import os
import re

# === Search Parameters - Edit these to customize your search ===
CHARACTER_FOLDER = "characters"
COG_INT_THRESHOLD = 34  # Combined minimum of COG + INT to match

def parse_aptitudes(file_content):
    """
    Parses aptitudes from the character text.
    Expects a section starting with 'Aptitudes:' followed by lines like '  COG: 10'
    Returns a dict of aptitudes { 'COG': int, 'INT': int, ... }
    """
    aptitudes = {}
    lines = file_content.splitlines()
    in_aptitudes_section = False

    for line in lines:
        if line.strip() == "Aptitudes:":
            in_aptitudes_section = True
            continue
        if in_aptitudes_section:
            if line.strip() == "" or not line.startswith("  "):
                # End of aptitudes section
                break
            # Expect line like "  COG: 10"
            match = re.match(r"\s*(\w+):\s*(\d+)", line)
            if match:
                apt_name = match.group(1)
                apt_value = int(match.group(2))
                aptitudes[apt_name] = apt_value

    return aptitudes

def find_characters_by_aptitudes():
    matched_characters = []

    if not os.path.exists(CHARACTER_FOLDER):
        print(f"Character folder '{CHARACTER_FOLDER}' does not exist.")
        return matched_characters

    for filename in os.listdir(CHARACTER_FOLDER):
        if filename.endswith(".txt"):
            filepath = os.path.join(CHARACTER_FOLDER, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                # Find character name from file or from Name: line
                char_name_match = re.search(r"^Name:\s*(.+)$", content, re.MULTILINE)
                char_name = char_name_match.group(1) if char_name_match else filename[:-4]

                aptitudes = parse_aptitudes(content)
                cog = aptitudes.get("COG", 0)
                inte = aptitudes.get("INT", 0)
                combined = cog + inte

                if combined > COG_INT_THRESHOLD:
                    matched_characters.append((char_name, combined))

    return matched_characters

if __name__ == "__main__":
    results = find_characters_by_aptitudes()
    print(f"Characters with COG + INT > {COG_INT_THRESHOLD}:")
    for name, total in results:
        print(f"  {name} (COG+INT = {total})")
