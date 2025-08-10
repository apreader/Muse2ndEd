import os
import sys
from PyPDF2 import PdfReader, PdfWriter

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
