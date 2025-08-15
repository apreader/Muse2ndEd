import os, json, re
from typing import Dict, List, Tuple, Optional

def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()

def parse_character_identity(txt_path: str) -> Dict[str, str]:
    ids = {"background":"", "career":"", "faction":"", "morph":"", "interest":"", "campaign_type":""}
    with open(txt_path, "r", encoding="utf-8-sig") as f:
        for raw in f:
            s = raw.strip()
            if not s: 
                continue
            lower = s.lower()
            if lower.startswith("background:"):
                ids["background"] = s.split(":",1)[1].strip()
            elif lower.startswith("career:"):
                ids["career"] = s.split(":",1)[1].strip()
            elif lower.startswith("faction:"):
                ids["faction"] = s.split(":",1)[1].strip()
            elif lower.startswith("morph:"):
                ids["morph"] = s.split(":",1)[1].strip()
            elif lower.startswith("interest:") or lower.startswith("interests:"):
                ids["interest"] = s.split(":",1)[1].strip()
            elif lower.startswith("campaign:") or lower.startswith("game type:") or lower.startswith("type of game:"):
                ids["campaign_type"] = s.split(":",1)[1].strip()
    return ids

def suggest_packs_for_character(txt_path: str, libraries_dir="libraries") -> List[Tuple[str,str]]:
    """Choose packs from Gear_Pack_Library.json based on exact Career and optional Campaign type.
       Returns list of (pack_name, source).
    """
    ids = parse_character_identity(txt_path)
    packs_path = os.path.join(libraries_dir, "Gear_Pack_Library.json")
    if not os.path.exists(packs_path):
        return []
    obj = _read_json(packs_path)
    prof = obj.get("Professions", {})
    camp = obj.get("Campaign", {})
    out = []

    # Exact Career → pack (if available)
    career = ids.get("career","").strip()
    if career and career in prof:
        out.append((career, "Gear_Pack_Library.json: Professions"))

    # Campaign type (optional in TXT)
    ctype = ids.get("campaign_type","").strip()
    if ctype and ctype in camp:
        out.append((ctype, "Gear_Pack_Library.json: Campaign"))

    # Fallbacks: if nothing matched, try light heuristic: Explorer→Explorer, Techie→Techie, etc.
    # (This is mostly redundant if file uses those exact keys.)
    if not out and career:
        # try case-insensitive match
        for k in prof.keys():
            if _norm(k) == _norm(career):
                out.append((k, "Gear_Pack_Library.json: Professions"))
                break

    # de-dup while preserving order
    seen=set(); final=[]
    for name,src in out:
        if name not in seen:
            seen.add(name); final.append((name,src))
    return final

def is_synth_morph(txt_path: str) -> bool:
    """Return True if the Morph line indicates a synthmorph."""
    ids = parse_character_identity(txt_path)
    m = ids.get("morph","")
    mlow = _norm(m)
    return ("synth" in mlow) or ("synthmorph" in mlow) or ("robot" in mlow)
