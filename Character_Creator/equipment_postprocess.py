import os
import re
import argparse
from typing import Dict, List, Tuple, Set
from Character_Creator.equipment_aggregator import aggregate_equipment
from Character_Creator.gear_pack_selector import suggest_packs_for_character

SECTION_HEADER = "\nEquipment:\n"

# Regex to remove an existing leading Gear Packs: [None] block (or any empty Gear Packs block)
_GEARPACKS_NONE_RE = re.compile(
    r'(?ms)^\s*Gear Packs:\s*\n\s*\[\s*None\s*\]\s*\n+', re.IGNORECASE
)

def _strip_redundant_gear_packs_block(text: str) -> str:
    # Remove "Gear Packs:\n  [None]\n\n" if present near the end or anywhere
    return _GEARPACKS_NONE_RE.sub("", text)

def _format_equipment_block(grouped: Dict[str, List[str]], packs_with_sources: List[Tuple[str,str]]) -> str:
    lines = [SECTION_HEADER.strip()]
    packs = [name for (name, _src) in packs_with_sources]
    if packs:
        lines.append("  Gear Packs:")
        for name in packs:
            lines.append(f"    {name}")
        lines.append("")
    for cat, items in grouped.items():
        if not items: 
            continue
        lines.append(f"  {cat}:")
        for it in items:
            lines.append(f"    {it}")
    lines.append("")
    return "\n".join(lines)

def append_equipment_to_txt(txt_path: str, libraries_path: str = "libraries", inplace: bool = True, out_path: str = None) -> str:
    # Auto-suggest packs from character identity (Background/Career/Faction/Morph/Interest/Campaign)
    suggestions = suggest_packs_for_character(txt_path, libraries_dir=libraries_path)
    # ensure at least one pack: prefer Career if selector didn't find any
    selected = {name for (name, _src) in suggestions}
    grouped, packs = aggregate_equipment(txt_path, libraries_path, selected_packs=selected)
    block = _format_equipment_block(grouped, packs)

    # Read existing content and strip redundant Gear Packs: [None]
    with open(txt_path, "r", encoding="utf-8") as f:
        original = f.read()
    cleaned = _strip_redundant_gear_packs_block(original)

    if inplace:
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(cleaned.rstrip() + "\n\n" + block)
        return txt_path
    else:
        if not out_path:
            root, ext = os.path.splitext(txt_path)
            out_path = root + "_with_equipment" + ext
        with open(out_path, "w", encoding="utf-8") as dst:
            dst.write(cleaned.rstrip() + "\n\n" + block)
        return out_path

def main():
    ap = argparse.ArgumentParser(description="Append grouped Equipment section to a Muse TXT")
    ap.add_argument("txt_path")
    ap.add_argument("--libraries", default="libraries")
    ap.add_argument("--inplace", action="store_true", help="Modify file in place (default false: write _with_equipment)")
    ap.add_argument("--out", default=None, help="Output path when not inplace")
    args = ap.parse_args()

    result = append_equipment_to_txt(args.txt_path, args.libraries, inplace=args.inplace, out_path=args.out)
    print(result)

if __name__ == "__main__":
    main()
