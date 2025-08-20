# -*- coding: utf-8 -*-
import os
import json
import re
from typing import Dict, Tuple, List, Set

# Use escaped Unicode so the file remains ASCII-safe on disk.
_PUNCT_RE = re.compile("[,:;()\\[\\]{}\\u2022\\u2013\\u2014-]")
_WS_RE = re.compile(r"\s+")
_COUNT_SUFFIX_RE = re.compile(r"\b(?:\d+\s*(?:doses?|dose|rounds?|round|rds|shots?|units?|mags?|magazines?|clip|clips)|pairs?|pair)\b$", re.IGNORECASE)

def _basic_normalize(name: str) -> str:
    s = name.lower().strip()
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s

def _remove_count_suffix(canon: str) -> str:
    return _WS_RE.sub(" ", _COUNT_SUFFIX_RE.sub("", canon)).strip()

def canonicalize_item_name(name: str, existing_names: Set[str]) -> str:
    """Canonicalize *name* using rules and existing canonical names set."""
    canon = _basic_normalize(name)
    base = _remove_count_suffix(canon)
    if base and base in existing_names:
        return base
    return canon

def _file_priority(fname: str) -> Tuple[int, str]:
    l = fname.lower()
    if "weapon" in l or "armor" in l:
        return (0, l)
    if any(k in l for k in ("ware", "chem", "mesh", "drone")):
        return (1, l)
    if "gear" in l:
        if any(x in l for x in ("all", "misc", "general", "catch")):
            return (2, l)
        return (1, l)
    return (2, l)

def build_gear_index(libraries_dir: str) -> Dict[str, Tuple[str, str]]:
    """Scan JSON libraries and return canonical name -> (relative file, entry key)."""
    records: List[Tuple[str, str, str, int, bool]] = []  # (file, entry_name, canon_basic, priority, has_suffix)
    for root, _dirs, files in os.walk(libraries_dir):
        for fname in files:
            if not fname.endswith('.json'):
                continue
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, libraries_dir)
            priority = _file_priority(rel)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"[gear_index] Warning: failed to load {rel}: {e}")
                continue
            items = []
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, dict):
                        items.append(k)
            elif isinstance(data, list):
                for obj in data:
                    if isinstance(obj, dict) and 'Name' in obj:
                        items.append(obj['Name'])
            for item in items:
                canon_basic = _basic_normalize(item)
                has_suffix = bool(_COUNT_SUFFIX_RE.search(canon_basic))
                records.append((rel, item, canon_basic, priority[0], has_suffix))
    exact_names: Set[str] = {r[2] for r in records if not r[4]}
    records.sort(key=lambda r: (r[3], r[0].lower(), r[1].lower()))
    index: Dict[str, Tuple[str, str]] = {}
    suffix_flags: Dict[str, bool] = {}
    for rel, item, canon_basic, _prio, has_suffix in records:
        canon = canonicalize_item_name(item, exact_names)
        existing = index.get(canon)
        if existing:
            existing_has_suffix = suffix_flags[canon]
            if has_suffix and not existing_has_suffix:
                continue
            if not has_suffix and existing_has_suffix:
                index[canon] = (rel, item)
                suffix_flags[canon] = False
            else:
                print(f"[gear_index] duplicate canonical name '{canon}' from {rel} / \"{item}\"; keeping first")
        else:
            index[canon] = (rel, item)
            suffix_flags[canon] = has_suffix
    return index
