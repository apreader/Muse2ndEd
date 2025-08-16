
# Character_Creator/gui_generate_action.py
# Runtime integrator for adding a "Generate Random Character…" menu entry to an existing Qt MainWindow.
# Safe: does not modify your existing ep2e_gui.py file. Just import and call attach_generate_random_action(window).
import os
from functools import partial

try:
    from PyQt5 import QtWidgets
except Exception:
    # Fallback to PySide2 if used
    try:
        from PySide2 import QtWidgets  # type: ignore
    except Exception:
        # Last-ditch: try PyQt6
        from PyQt6 import QtWidgets  # type: ignore

from library_manager import LibraryManager
from muse_parser import parse_character_txt

# Accept both signatures for save_character_to_file (char) and (char, lm)
from Character_Creator.generate_random_character import generate_random_character
from Character_Creator.save_character_to_file import save_character_to_file


def _safe_save_character(char, lm):
    try:
        save_character_to_file(char, lm)  # some versions expect (char, lm)
    except TypeError:
        save_character_to_file(char)      # others expect just (char)


def _generate_and_load(window):
    name, ok = QtWidgets.QInputDialog.getText(window, "Generate Random Character", "Enter character name:")
    if not ok or not str(name).strip():
        return
    name = str(name).strip()

    try:
        lm = LibraryManager()
        lm.load_all_libraries()

        char = generate_random_character(name, lm)
        _safe_save_character(char, lm)

        path = os.path.join(os.getcwd(), "characters", f"{name}.txt")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Expected character file not found: {path}")

        # Load into GUI — expect window to provide these
        if hasattr(window, "log"):
            window.log(f"Loading generated character from: {path}")
        parsed = parse_character_txt(path)

        # Common field names used by many builds of this GUI
        setattr(window, "character", parsed)
        setattr(window, "current_file", path)

        # Try common refresh methods if present
        for meth in ("refresh_overview", "populate_skills", "populate_equipment", "populate_traits"):
            if hasattr(window, meth) and callable(getattr(window, meth)):
                try:
                    getattr(window, meth)()
                except Exception:
                    pass

        QtWidgets.QMessageBox.information(window, "Character Generated", f"Character '{name}' generated and loaded.")
    except Exception as e:
        QtWidgets.QMessageBox.critical(window, "Generation Failed", f"{type(e).__name__}: {e}")


def attach_generate_random_action(window):
    """Attach a 'Generate Random Character…' menu action to an existing MainWindow.

    This function is conservative: it looks for an existing menubar and 'File' menu;
    if not found, it creates one. It doesn't overwrite existing actions.
    """
    if hasattr(window, "menuBar"):
        menubar = window.menuBar()
    else:
        menubar = None

    if menubar is None:
        # Create a minimal menu bar if one does not exist
        menubar = QtWidgets.QMenuBar(window)
        window.setMenuBar(menubar)

    # Try to find a 'File' menu; create if missing
    file_menu = None
    for act in menubar.actions():
        menu = act.menu()
        if menu and menu.title().lower().strip("&") == "file":
            file_menu = menu
            break

    if file_menu is None:
        file_menu = menubar.addMenu("File")

    # Prevent duplicates if attach is called multiple times
    for act in file_menu.actions():
        if act.text().lower().startswith("generate random character"):
            return

    action = QtWidgets.QAction("Generate Random Character…", window)
    action.triggered.connect(partial(_generate_and_load, window))
    # Prefer to put it at the top for visibility
    file_menu.insertAction(file_menu.actions()[0] if file_menu.actions() else None, action)
