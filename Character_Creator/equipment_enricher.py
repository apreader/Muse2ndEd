# -*- coding: utf-8 -*-
import os
import json
import tempfile
import re
from typing import Dict, List, Tuple, Any

from Character_Creator.gear_index import build_gear_index, canonicalize_item_name

_START_SENTINEL = "<<<EQUIPMENT_DETAILS_START>>>"
_END_SENTINEL = "<<<EQUIPMENT_DETAILS_END>>>"

_KNOWN_CATEGORIES = {
    "Weapons",
    "Armor",
    "Gear",
    "Ware",
    "Drones",
    "Chems",
    "Mesh",
    "Other",
}

_EM_DASH = "\u2014"
_BULLET = "\u2022"
_WS_RE = re.compile(r"\s+")

def _one_line(s: Any) -> str:
    s = "" if s is None else str(s)
    return _WS_RE.sub(" ", s).strip()

def _truncate(s: str, n: int) -> str:
    s = s or ""
    return s if len(s) <= n else (s[: max(0, n-1)].rstrip() + "…")

# --------------------- Description picking & synthesis ---------------------

def _pick_description(entry: Dict, category: str, synth_max: int = 220) -> str:
    """Choose the best description from Description -> Long -> Short -> Effects/Bonuses/Functions/Use/Usage/Notes.
    If none, synthesize from key stats.

    Returns a one-line, truncated description.

    """
    if not isinstance(entry, dict):
        return ""
    for key in ("Description", "Long", "Short", "Effects", "Bonuses", "Function", "Functions", "Use", "Usage", "Notes"):
        if entry.get(key):
            return _truncate(_one_line(entry.get(key, "")), synth_max)

    cat = (category or "").lower()
    bits = []
    if cat == "weapons":
        if entry.get("Damage"): bits.append(f"Damage {entry['Damage']}")
        if entry.get("AP"): bits.append(f"AP {entry['AP']}")
        if entry.get("Firing Modes"): bits.append(f"Modes {entry['Firing Modes']}")
        if entry.get("Range"): bits.append(f"Range {entry['Range']}")
        if entry.get("Ammo"): bits.append(f"Ammo {entry['Ammo']}")
    elif cat == "armor":
        e = entry.get("Energy"); k = entry.get("Kinetic")
        if e is not None or k is not None:
            e = e if e is not None else 0
            k = k if k is not None else 0
            bits.append(f"E+{e} / K+{k}")
    else:
        # Generic items: stitch common fields
        for key in ("Type", "Model", "Movement", "Speed", "Capacity", "Rating"):
            if entry.get(key):
                bits.append(f"{key}: {_one_line(entry[key])}")
        if entry.get("Armor"):
            bits.append(f"Armor: {_one_line(entry['Armor'])}")
        for key in ("WT","DUR","DR"):
            if entry.get(key) is not None:
                bits.append(f"{key}: {_one_line(entry[key])}")
        if entry.get("Complexity/GP"):
            bits.append(f"GP: {_one_line(entry['Complexity/GP'])}")
        if entry.get("Complexity/GP (per 100)"):
            bits.append(f"GP(100): {_one_line(entry['Complexity/GP (per 100)'])}")
        if entry.get("Ware"):
            ware = entry["Ware"]
            if isinstance(ware, list) and ware:
                bits.append("Ware: " + ", ".join(_one_line(w) for w in ware[:6]) + ("" if len(ware)<=6 else f" (+{len(ware)-6} more)"))
    desc = "; ".join(bits)
    return _truncate(_one_line(desc), synth_max)

# ----------------------- JSON entry loading (deep) ------------------------

def _iter_named_objects(data: Any):
    """Yield (obj) for any dict with a 'Name' field inside arbitrary JSON structures."""
    if isinstance(data, dict):
        # direct object with Name
        if "Name" in data:
            yield data
        # Walk dict values
        for v in data.values():
            for o in _iter_named_objects(v):
                yield o
    elif isinstance(data, list):
        for item in data:
            for o in _iter_named_objects(item):
                yield o

def _find_by_name_deep(data: Any, name: str):
    low = (name or "").strip().lower()
    for obj in _iter_named_objects(data):
        if _one_line(obj.get("Name","")).lower() == low:
            return obj
    return None

def _load_json_entry(libraries_dir: str, rel_path: str, entry_key: str):
    """Load a library object by rel path and name, searching deeply (handles nested Entries)."""
    path = os.path.join(libraries_dir, rel_path)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return None
    obj = _find_by_name_deep(data, entry_key)
    return obj

# --------------------------- Detail extraction ----------------------------

def _parse_armor_string(armor_val: Any):
    s = _one_line(armor_val)
    if "/" in s:
        parts = [p.strip() for p in s.split("/", 1)]
        try:
            e = int(parts[0])
        except Exception:
            e = parts[0]
        try:
            k = int(parts[1])
        except Exception:
            k = parts[1]
        return e, k
    return None, None

def _extract_generic_stat_bullets(entry: Dict) -> List[str]:
    """Return a list of generic bullets for common fields across gear, bots, drones, ware, etc."""
    bullets: List[str] = []
    # Complexity/GP
    if entry.get("Complexity/GP"):
        bullets.append(f"GP: {_one_line(entry['Complexity/GP'])}")
    if entry.get("Complexity/GP (per 100)"):
        bullets.append(f"GP (per 100): {_one_line(entry['Complexity/GP (per 100)'])}")
    # Stat block
    for key in ("Vigor","Flex","WT","DUR","DR","Size","Movement","Speed","Capacity","Rating","Type","Model"):
        if entry.get(key) not in (None, "", []):
            bullets.append(f"{key}: {_one_line(entry[key])}")
    # Armor field (string like '16/12')
    if entry.get("Armor"):
        e,k = _parse_armor_string(entry.get("Armor"))
        if e is not None or k is not None:
            bullets.append(f"Armor: E+{e} / K+{k}")
        else:
            bullets.append(f"Armor: {_one_line(entry['Armor'])}")
    # Ware
    ware = entry.get("Ware")
    if isinstance(ware, list) and ware:
        shown = ", ".join(_one_line(w) for w in ware[:10])
        if len(ware) > 10:
            shown += f" (+{len(ware)-10} more)"
        bullets.append(f"Ware: {shown}")
    return bullets

def _extract_details(category: str, entry: Dict) -> List[str]:
    cat = (category or "").lower()
    details: List[str] = []
    if cat == "weapons":
        dv = entry.get("DV") or entry.get("Damage")
        if dv:
            details.append(f"DV: {dv}")
        if entry.get("AP"):
            details.append(f"AP: {entry['AP']}")
        if entry.get("Firing Modes"):
            details.append(f"Firing Modes: {entry['Firing Modes']}")
        if entry.get("Range"):
            details.append(f"Range: {entry['Range']}")
        if entry.get("Ammo"):
            details.append(f"Ammo: {entry['Ammo']}")
        # Also capture non-gun ammo/accessory fields if present
        if entry.get("Modifier"):
            details.append(f"Modifier: {entry['Modifier']}")
        if entry.get("Complexity/GP"):
            details.append(f"GP: {entry['Complexity/GP']}")
        if entry.get("Complexity/GP (per 100)"):
            details.append(f"GP (per 100): {entry['Complexity/GP (per 100)']}")
        if entry.get("Notes"):
            details.append(f"Notes: {entry['Notes']}")
    elif cat == "armor":
        e = entry.get("Energy")
        k = entry.get("Kinetic")
        if e is not None or k is not None:
            e = e if e is not None else 0
            k = k if k is not None else 0
            details.append(f"Armor: E+{e} / K+{k}")
        if entry.get("Notes"):
            details.append(f"Notes: {entry['Notes']}")
    else:
        # Generic extraction for bots/drones/gear/etc.
        details.extend(_extract_generic_stat_bullets(entry))

    # Always include Description at end (picked or synthesized)
    desc = _pick_description(entry, cat, synth_max=220)
    if desc:
        details.append(f"Description: {desc}")
    return details

# ----------------------------- TXT parsing --------------------------------

def _parse_equipment(lines: List[str]) -> Dict[str, List[str]]:
    equipment: Dict[str, List[str]] = {}
    category = None
    for line in lines:
        if line.startswith("  "):
            stripped = line.strip()
            if stripped.endswith(":"):
                category = stripped[:-1]
                if category not in _KNOWN_CATEGORIES:
                    category = "Gear"
                equipment.setdefault(category, [])
            elif category:
                equipment.setdefault(category, []).append(stripped)
        elif line.strip() == "":
            continue
        else:
            break
    return equipment

def _split_equipment_section(text: str) -> Tuple[str, List[str], str]:
    lines = text.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "Equipment:":
            start_idx = i
            break
    if start_idx is None:
        return text, [], ""
    before = "\n".join(lines[: start_idx + 1])
    after_lines = lines[start_idx + 1 :]
    equip_lines: List[str] = []
    for j, line in enumerate(after_lines):
        if line.startswith(_START_SENTINEL):
            after = "\n".join(after_lines[j:])
            break
        if line and not line.startswith(" ") and line.strip() != "":
            after = "\n".join(after_lines[j:])
            break
        equip_lines.append(line)
    else:
        after = ""
    return before, equip_lines, after

# ------------------------------- Main op ----------------------------------

def enrich_equipment_txt(txt_path: str, libraries_dir: str) -> None:
    if not os.path.exists(txt_path) or not os.path.isdir(libraries_dir):
        return
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            original = f.read()
    except Exception:
        return

    # Remove any previous generated block before re-writing
    if _START_SENTINEL in original and _END_SENTINEL in original:
        pre, rest = original.split(_START_SENTINEL, 1)
        _, post = rest.split(_END_SENTINEL, 1)
        base_text = pre + post
    else:
        base_text = original

    before, equip_lines, after = _split_equipment_section(base_text)
    if not equip_lines:
        return

    equipment = _parse_equipment(equip_lines)
    index = build_gear_index(libraries_dir)
    index_keys = set(index.keys())

    found: Dict[str, List[Tuple[str, List[str]]]] = {}
    not_found: List[str] = []

    for cat, items in equipment.items():
        for line in items:
            display = line.split(_EM_DASH)[0].strip()
            canon = canonicalize_item_name(display, index_keys)
            entry_info = index.get(canon)
            if not entry_info:
                not_found.append(display)
                continue
            rel_file, entry_key = entry_info
            entry = _load_json_entry(libraries_dir, rel_file, entry_key)
            if not isinstance(entry, dict):
                not_found.append(display)
                continue

            # Add some trace metadata for downstream (optional)
            entry = dict(entry)
            entry.setdefault("_source_file", rel_file)

            details = _extract_details(cat, entry)
            details.append(f"Source: {rel_file} / \"{entry_key}\"")
            found.setdefault(cat, []).append((entry.get("Name", display), details))

    lines_out: List[str] = ["=== Equipment Details (Generated) ==="]
    for cat in ("Weapons", "Armor", "Gear", "Ware", "Drones", "Chems", "Mesh", "Other"):
        items = found.get(cat)
        if not items:
            continue
        lines_out.append(f"[{cat}]")
        for name, details in items:
            lines_out.append(f"- {name}")
            for d in details:
                lines_out.append(f"  {_BULLET} {d}")
        lines_out.append("")

    if not_found:
        lines_out.append("[Not Found]")
        for name in not_found:
            lines_out.append(f"- {name}")
        lines_out.append("")

    block_text = "\n".join(lines_out).rstrip() + "\n"
    wrapped = f"{_START_SENTINEL}\n{block_text}{_END_SENTINEL}"

    if _START_SENTINEL in original and _END_SENTINEL in original:
        start = original.index(_START_SENTINEL)
        end = original.index(_END_SENTINEL) + len(_END_SENTINEL)
        new_text = original[:start] + wrapped + original[end:]
    else:
        new_text = original.rstrip() + "\n\n" + wrapped + "\n"

    dir_name = os.path.dirname(txt_path)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(new_text)
        os.replace(tmp_path, txt_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
