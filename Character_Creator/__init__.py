"""
Character_Creator package initializer — clean (no debug prints).

Keeps the post-save hook that appends a grouped Equipment section to the end
of each saved TXT, using equipment_postprocess.append_equipment_to_txt.
The hook is repo-root aware and falls back to the newest TXT in <repo_root>/characters
if the exact path cannot be inferred from the save call.
"""

import os
import functools

# Resolve repo root as the parent of this package directory
_PKG_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_PKG_DIR, os.pardir))
_CHAR_DIR = os.path.join(_REPO_ROOT, "characters")
_LIBS_DIR = os.path.join(_REPO_ROOT, "libraries")

# Import original save function module
try:
    from . import save_character_to_file as _save_mod
except Exception:
    _save_mod = None

# Import appender
try:
    from .equipment_postprocess import append_equipment_to_txt as _append_eq
except Exception:
    _append_eq = None

def _newest_txt(char_dir: str):
    try:
        if not os.path.isdir(char_dir):
            return None
        txts = [os.path.join(char_dir, f) for f in os.listdir(char_dir) if f.lower().endswith(".txt")]
        if not txts:
            return None
        txts.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return txts[0]
    except Exception:
        return None

def _hook_save():
    if _save_mod is None or _append_eq is None:
        return
    orig = getattr(_save_mod, "save_character_to_file", None)
    if not callable(orig):
        return

    @functools.wraps(orig)
    def wrapper(*args, **kwargs):
        # Snapshot newest txt BEFORE save
        try:
            before_newest = _newest_txt(_CHAR_DIR)
            before_mtime = os.path.getmtime(before_newest) if before_newest and os.path.exists(before_newest) else 0.0
        except Exception:
            before_mtime = 0.0

        # Call original save
        result = orig(*args, **kwargs)

        # Try to get path directly from args/kwargs
        path = kwargs.get("path") or kwargs.get("filepath")
        if path is None and len(args) >= 2 and isinstance(args[1], str):
            path = args[1]

        # Determine target
        target_path = None
        if isinstance(path, str) and os.path.isfile(path):
            target_path = path
        else:
            newest = _newest_txt(_CHAR_DIR)
            try:
                if newest and (before_mtime == 0.0 or os.path.getmtime(newest) >= before_mtime):
                    target_path = newest
            except Exception:
                target_path = newest

        # Append equipment (silent on failure)
        if target_path:
            try:
                _append_eq(target_path, libraries_path=_LIBS_DIR, inplace=True)
            except Exception:
                pass

        return result

    setattr(_save_mod, "save_character_to_file", wrapper)

try:
    _hook_save()
except Exception:
    # Stay silent if hooking fails
    pass
