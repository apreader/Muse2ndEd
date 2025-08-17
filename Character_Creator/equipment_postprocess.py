import os
import re
import argparse
from typing import Dict, List, Tuple, Set
from Character_Creator.equipment_aggregator import aggregate_equipment
from Character_Creator.gear_pack_selector import suggest_packs_for_character


def _load_all_library_items(libraries_dir: str) -> Dict[str, Dict]:
    """Build a name->details dict across Gear_Library and Weapon_Library."""
    import json, os
    details = {}
    # Gear_Library
    gear_dir = os.path.join(libraries_dir, "Gear_Library")
    if os.path.isdir(gear_dir):
        for fn in os.listdir(gear_dir):
            if fn.endswith(".json"):
                try:
                    arr = json.load(open(os.path.join(gear_dir, fn), "r", encoding="utf-8"))
                    # can be dict of categories -> list, or list
                    if isinstance(arr, dict):
                        for _cat, items in arr.items():
                            if isinstance(items, list):
                                for it in items:
                                    if isinstance(it, dict) and "Name" in it:
                                        details.setdefault(it["Name"], {}).update(it)
                    elif isinstance(arr, list):
                        for it in arr:
                            if isinstance(it, dict) and "Name" in it:
                                details.setdefault(it["Name"], {}).update(it)
                except Exception:
                    pass
    # Weapon_Library
    w_dir = os.path.join(libraries_dir, "Weapon_Library")
    if os.path.isdir(w_dir):
        for fn in os.listdir(w_dir):
            if fn.endswith(".json"):
                try:
                    arr = json.load(open(os.path.join(w_dir, fn), "r", encoding="utf-8"))
                    if isinstance(arr, list):
                        for it in arr:
                            if isinstance(it, dict) and "Name" in it:
                                details.setdefault(it["Name"], {}).update(it)
                except Exception:
                    pass
    return details

def _format_item_line(name: str, details: Dict) -> str:
    """Return a neat single-line summary with stats."""
    d = details or {}
    # Weapon?
    if any(k in d for k in ("Damage","Firing Modes","Ammo","Range")):
        bits = [name]
        if d.get("Damage"): bits.append(f"DV {d['Damage']}")
        if d.get("Firing Modes"): bits.append(f"FM {d['Firing Modes']}")
        if d.get("Range"): bits.append(f"Rng {d['Range']}")
        if d.get("Ammo"): bits.append(f"Ammo {d['Ammo']}")
        if d.get("Notes"): bits.append(f"({d['Notes']})")
        return " — ".join([bits[0], ", ".join(bits[1:])]) if len(bits) > 1 else bits[0]
    # Armor?
    if "Energy" in d or "Kinetic" in d:
        e = d.get("Energy"); k = d.get("Kinetic")
        bits = [name]
        if e is not None and k is not None:
            bits.append(f"Armor E{e}/K{k}")
        elif e is not None:
            bits.append(f"Armor E{e}")
        elif k is not None:
            bits.append(f"Armor K{k}")
        if d.get("Notes"): bits.append(f"({d['Notes']})")
        return " — ".join([bits[0], ", ".join(bits[1:])]) if len(bits) > 1 else bits[0]
    # Generic gear with Description
    if d.get("Description"):
        return f"{name} — {d['Description']}"
    # Fallback
    return name

def _format_equipment_block_rich(grouped: Dict[str, List[str]], packs_with_sources: List[Tuple[str,str]], libraries_dir: str) -> str:
    details = _load_all_library_items(libraries_dir)
    lines = [SECTION_HEADER.strip()]
    packs = [name for (name, _src) in packs_with_sources]
    if packs:
        lines.append("  Gear Packs:")
        for name in packs:
            lines.append(f"    {name}")
        lines.append("")
    for cat in sorted(grouped.keys()):
        items = grouped.get(cat) or []
        if not items: 
            continue
        lines.append(f"  {cat}:")
        for it in items:
            line = _format_item_line(it, details.get(it, {}))
            lines.append(f"    {line}")
    lines.append("")
    return "\n".join(lines)
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
    # --- Enrich weapons & armor and mirror minimal keys for PDF ---
    try:
        grouped, packs = aggregate_equipment(txt_path, libraries_dir=libraries_path, selected_packs=set(suggestions))
        details = _load_all_library_items(libraries_path)
        enriched = _enrich_weapons_and_armor(grouped, details)
    except Exception:
        enriched = {}

    # Build 'Weapon 1.*' and 'Armor.*' lines (top-level keys), outside any sections
    top_level_lines = []
    # Insert top-level keys for PDF consumption (if any)
    if top_level_lines:
        for _ln in top_level_lines:
            lines.append(_ln)
        lines.append("")
    if enriched.get("weapons"):
        w1 = enriched["weapons"][0]
        top_level_lines.append(f"Weapon 1.Name: {w1.get('name','')}")
        top_level_lines.append(f"Weapon 1.DV: {w1.get('dv','')}")
        top_level_lines.append(f"Weapon 1.Modes: {w1.get('firing_modes','')}")
        top_level_lines.append(f"Weapon 1.Ammo: {w1.get('ammo','')}")
        if len(enriched["weapons"]) > 1:
            w2 = enriched["weapons"][1]
            top_level_lines.append(f"Weapon 2.Name: {w2.get('name','')}")
            top_level_lines.append(f"Weapon 2.DV: {w2.get('dv','')}")
            top_level_lines.append(f"Weapon 2.Modes: {w2.get('firing_modes','')}")
            top_level_lines.append(f"Weapon 2.Ammo: {w2.get('ammo','')}")
    if enriched.get("armor"):
        a = enriched["armor"]
        top_level_lines.append(f"Armor.Name: {a.get('name','')}")
        top_level_lines.append(f"Armor.EK: {a.get('energy',0)} / {a.get('kinetic',0)}")


    # ensure at least one pack: prefer Career if selector didn't find any
    selected = {name for (name, _src) in suggestions}
    grouped, packs = aggregate_equipment(txt_path, libraries_path, selected_packs=selected)
    block = _format_equipment_block_rich(grouped, packs, libraries_path)

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


def _parse_int_from_str(val):
    try:
        if isinstance(val, int):
            return val
        if not isinstance(val, str):
            return 0
        s = val.strip()
        s = s.replace("+","")
        return int(s)
    except Exception:
        return 0

def _enrich_weapons_and_armor(grouped: Dict[str, List[str]], details: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    Returns a dict with keys:
      - 'weapons': list of dicts [{name, category, dv, ap, ammo, firing_modes, range, traits}]
      - 'armor': dict {name, energy, kinetic, armor_type, mods_applied: [names]}
    """
    enriched = {"weapons": [], "armor": None}

    # Build quick lookups for armor types and mods
    armor_type_names = set()
    armor_mod_names = set()
    for nm, d in details.items():
        if d.get("_source_file") == "wlibrary_armor_types.json":
            armor_type_names.add(nm)
        if d.get("_source_file") == "wlibrary_armor_mods.json":
            armor_mod_names.add(nm)

    # Weapons from grouped catalog
    for nm in grouped.get("Weapons", []):
        d = details.get(nm, {})
        if not d:
            continue
        # Heuristic: treat as weapon if it has obvious weapon fields
        if any(k in d for k in ("Damage","Firing Modes","Ammo","Range")) and nm not in armor_type_names and nm not in armor_mod_names:
            category = (d.get("Category") or d.get("_weapon_category") or "").lower()
            dv = d.get("Damage", "")
            ap = d.get("AP", "") if isinstance(d.get("AP",""), str) else ""
            fm = d.get("Firing Modes", "")
            ammo = d.get("Ammo", "")
            rng = d.get("Range", "")
            traits = []
            if d.get("Notes"):
                traits.append(d["Notes"])
            enriched["weapons"].append({
                "name": nm,
                "category": category,
                "dv": dv,
                "ap": ap,
                "ammo": ammo,
                "firing_modes": fm,
                "range": rng,
                "traits": traits,
            })

    # Armor: pick first seen armor type in the assembled items
    all_items = []
    for lst in grouped.values():
        all_items.extend(lst)

    base_armor_name = None
    for nm in all_items:
        if nm in armor_type_names:
            base_armor_name = nm
            break

    if base_armor_name:
        base = details.get(base_armor_name, {}) or {}
        e = _parse_int_from_str(base.get("Energy"))
        k = _parse_int_from_str(base.get("Kinetic"))
        mods_applied = []
        # Apply any armor mods present in the full items list
        for nm in all_items:
            if nm in armor_mod_names:
                md = details.get(nm, {}) or {}
                e += _parse_int_from_str(md.get("Energy"))
                k += _parse_int_from_str(md.get("Kinetic"))
                mods_applied.append(nm)
        enriched["armor"] = {
            "name": base_armor_name,
            "energy": e,
            "kinetic": k,
            "armor_type": base.get("Ware Type", "-"),
            "mods_applied": mods_applied,
        }

    return enriched
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
