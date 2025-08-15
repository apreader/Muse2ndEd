import os, json, re
from typing import Dict, List, Tuple, Set, Optional, Any

def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _extract_names_from_json(obj: Any) -> List[str]:
    names: List[str] = []
    if isinstance(obj, list):
        for it in obj:
            if isinstance(it, dict):
                for k in ("Name","name","title","Title"):
                    if k in it and isinstance(it[k], str):
                        names.append(it[k]); break
                else:
                    if "id" in it and isinstance(it.get("id"), str):
                        names.append(it["id"])
            elif isinstance(it, str):
                names.append(it)
    elif isinstance(obj, dict):
        if "items" in obj and isinstance(obj["items"], list):
            names.extend(_extract_names_from_json(obj["items"]))
        else:
            # Fallback: treat keys as item names if values look like item dicts/strings
            for k,v in obj.items():
                if isinstance(v, (dict, list, str)):
                    names.append(str(k))
    return list(dict.fromkeys(names))

def _normalize(s: str) -> str:
    return re.sub(r"\\s+", " ", (s or "").strip()).lower()

def _collect_packs_from_tree(node, pack_map: Dict[str, List[str]], source_map: Dict[str,str], default_source: str):
    """Walk nested dict/list; whenever we hit a pack-like node, record it:
       - dict with 'items' list
       - dict key -> list of strings (items)
    """
    if isinstance(node, dict):
        # Case 1: direct pack dict with items list
        if "items" in node and isinstance(node["items"], list):
            # need a name for this node; caller should have set it via outer loop; we won't handle anonymous here
            pass
        for k, v in node.items():
            # Case 2: key -> list of items
            if isinstance(v, list) and v and all(isinstance(x, (str, dict)) for x in v):
                pack_map[k] = _extract_names_from_json(v)
                source_map[k] = default_source
            # Case 3: nested dict; recurse
            _collect_packs_from_tree(v, pack_map, source_map, default_source)
    elif isinstance(node, list):
        for v in node:
            _collect_packs_from_tree(v, pack_map, source_map, default_source)

def load_catalogs(libraries_dir="libraries"):
    """Build item catalog (name->category), gear_packs (pack->items), pack_sources (pack->source)."""
    categories_by_file = {
        "glibrary_augmentations": "Ware",
        "glibrary_gear": "Gear",
        "glibrary_bots": "Drones",
        "glibrary_vehicles": "Vehicles",
        "clibrary_creatures": "Creatures",
        "glibrary_services": "Services",
        "glibrary_mesh": "Mesh",
        "glibrary_chems": "Chems",
        "wlibrary_": "Weapons",
    }

    item_catalog: Dict[str,str] = {}
    gear_packs: Dict[str,List[str]] = {}
    pack_sources: Dict[str,str] = {}

    # Gear Packs (supports nested structure like {"Professions": {...}, "Campaign": {...}})
    packs_path = os.path.join(libraries_dir, "Gear_Pack_Library.json")
    if os.path.exists(packs_path):
        try:
            packs_json = _read_json(packs_path)
            _collect_packs_from_tree(packs_json, gear_packs, pack_sources, default_source="Gear_Pack_Library.json")
        except Exception:
            pass

    # Gear Library folder
    gear_lib_dir = os.path.join(libraries_dir, "Gear_Library")
    if os.path.isdir(gear_lib_dir):
        for fn in os.listdir(gear_lib_dir):
            if not fn.endswith(".json"): continue
            stem = os.path.splitext(fn)[0]
            category = None
            for prefix, cat in categories_by_file.items():
                if stem.startswith(prefix):
                    category = cat; break
            category = category or "Other"
            try:
                obj = _read_json(os.path.join(gear_lib_dir, fn))
                names = _extract_names_from_json(obj)
                for nm in names:
                    item_catalog[nm] = category
            except Exception:
                continue

    # Weapon library
    weapon_dir = os.path.join(libraries_dir, "Weapon_Library")
    if os.path.isdir(weapon_dir):
        for fn in os.listdir(weapon_dir):
            if not fn.endswith(".json"): continue
            try:
                obj = _read_json(os.path.join(weapon_dir, fn))
                names = _extract_names_from_json(obj)
                for nm in names:
                    item_catalog[nm] = "Weapons"
            except Exception:
                continue

    return item_catalog, gear_packs, pack_sources

def parse_character_txt_for_packs_and_items(path, known_packs, known_items):
    packs = set()
    items = set()
    known_pack_norm = { _normalize(p): p for p in known_packs }
    known_item_norm = { _normalize(i): i for i in known_items }

    with open(path, "r", encoding="utf-8-sig") as f:
        for raw in f:
            s = raw.strip()
            if not s: continue
            label = s.split(":",1)[0].strip()
            low = _normalize(s)
            for knorm, original in known_pack_norm.items():
                if knorm in low:
                    packs.add(original)
            for knorm, original in known_item_norm.items():
                if knorm in low or knorm == _normalize(label):
                    items.add(original)

    return packs, items

def expand_packs_to_items(selected_packs, gear_packs):
    items = set()
    for p in selected_packs:
        for it in gear_packs.get(p, []):
            items.add(it)
    return items

CATEGORY_OVERRIDES = {
    # Common corrections
    "Utilitool": "Gear",
    "Tools (Kit)": "Gear",
    "Private Server": "Mesh",
    "Exploit App": "Mesh",
    "E-Veil": "Mesh",
    "Guardian Angel": "Drones",
    "Gnat": "Drones",
    "Smart Hawk": "Drones",
    "Fixer Swarm": "Drones",
    "Docbot": "Drones",
    "Automech": "Drones",
    "Medium Fabber": "Gear",
    "Healing Vat": "Gear",
    "Healing Spray": "Chems",
    "Meds (5 doses)": "Chems",
    "Fokus (5 doses)": "Chems",
    "Stiff (5 doses)": "Chems",
    "Enhanced Security": "Gear",
    "Nanodetector": "Gear",
    "Med Scanner": "Gear",
    "Electrical Sense": "Ware",
    "Enhanced Hearing": "Ware",
    "Neuromodulation": "Ware",
    "Drone Rig": "Ware",
}

def group_items_by_category(items, item_catalog):
    groups = {}
    for it in items:
        cat = CATEGORY_OVERRIDES.get(it, item_catalog.get(it, "Other"))
        groups.setdefault(cat, []).append(it)
    for cat in groups:
        groups[cat] = sorted(list(set(groups[cat])))
    ordered = ["Ware","Weapons","Gear","Drones","Vehicles","Creatures","Chems","Mesh","Services","Other"]
    result = {c: groups[c] for c in ordered if c in groups}
    for c in sorted(set(groups.keys()) - set(ordered)):
        result[c] = groups[c]
    return result

def aggregate_equipment(character_txt_path: str, libraries_dir="libraries", selected_packs: Optional[Set[str]] = None):
    item_catalog, gear_packs, pack_sources = load_catalogs(libraries_dir)
    known_items = list(item_catalog.keys())
    known_packs = list(gear_packs.keys())

    packs_detected, items_explicit = parse_character_txt_for_packs_and_items(character_txt_path, known_packs, known_items)
    packs_final = set(packs_detected)
    if selected_packs:
        packs_final |= set(selected_packs)

    items_from_packs = expand_packs_to_items(packs_final, gear_packs)
    all_items = set(items_from_packs) | set(items_explicit)
    grouped = group_items_by_category(all_items, item_catalog)

    packs_with_sources = [(p, pack_sources.get(p, "Gear_Pack_Library.json")) for p in sorted(packs_final)]
    return grouped, packs_with_sources

if __name__ == "__main__":
    # tiny smoke test when run directly
    import argparse, json as _json
    ap = argparse.ArgumentParser()
    ap.add_argument("character_txt")
    ap.add_argument("--libraries", default="libraries")
    ap.add_argument("--print", action="store_true")
    args = ap.parse_args()
    g,p = aggregate_equipment(args.character_txt, args.libraries)
    if args.print:
        if p:
            print("Gear Packs:")
            for n,s in p:
                print(f"  {n} (Source: {s})")
            print("")
        for cat, items in g.items():
            print(cat+":")
            for it in items:
                print("  "+it)
    else:
        print(_json.dumps({"packs": p, "grouped": g}, indent=2, ensure_ascii=False))
