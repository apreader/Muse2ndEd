
# ep2e_gui_wrapper.py
# Launches your existing ep2e_gui.MainWindow, then injects the Generate Random Character action at runtime.
import sys
import traceback

# Try multiple Qt bindings; prefer PyQt5
try:
    from PyQt5 import QtWidgets
except Exception:
    try:
        from PySide2 import QtWidgets  # type: ignore
    except Exception:
        from PyQt6 import QtWidgets  # type: ignore

# Import your existing GUI module and window class
import ep2e_gui

# Find a plausible MainWindow class
MainWindowClass = None
for name in dir(ep2e_gui):
    obj = getattr(ep2e_gui, name)
    try:
        import inspect
        if inspect.isclass(obj):
            # Rough heuristic: subclass of QMainWindow
            from PyQt5 import QtWidgets as _QtWidgets
            if issubclass(obj, _QtWidgets.QMainWindow):
                MainWindowClass = obj
                break
    except Exception:
        pass

if MainWindowClass is None:
    # Fallback: look for a callable factory returning a main window
    if hasattr(ep2e_gui, "create_main_window") and callable(ep2e_gui.create_main_window):
        MainWindowClass = None  # we'll call factory
    else:
        raise RuntimeError("Could not locate a QMainWindow subclass or factory in ep2e_gui.py")

from Character_Creator.gui_generate_action import attach_generate_random_action

def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    if MainWindowClass is not None:
        window = MainWindowClass()
    else:
        # Factory path
        window = ep2e_gui.create_main_window()

    # Attach integration
    attach_generate_random_action(window)

    window.show()
    sys.exit(app.exec_() if hasattr(app, 'exec_') else app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        raise
