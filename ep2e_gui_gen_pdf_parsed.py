
import sys
import os
import datetime
from PyQt5 import QtWidgets, QtCore

from muse_parser import parse_character_txt, serialize_character_txt
from systems.roll_core import roll_d100, evaluate_roll, fmt_roll_for_display, make_total
from systems.stress_tests import apply_stress_and_trauma, stress_outcome_summary
from systems.remorphing import remorph_roll, remorph_outcome_summary
from systems.pools import list_pools, spend_pool, get_pool, set_pool
from systems.combat import build_attack_target, resolve_attack_vs_defense, apply_damage_after_armor, apply_damage_to_character

# --- NEW: generator imports ---
from library_manager import LibraryManager
from Character_Creator.generate_random_character import generate_random_character
from Character_Creator.save_character_to_file import save_character_to_file

# --- NEW: simple dialog for generation ---
class GenerateDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Random Character")
        self.setModal(True)
        v = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self.name_edit = QtWidgets.QLineEdit()
        self.cb_pdf = QtWidgets.QCheckBox("Also export to PDF after generation")
        form.addRow("Name:", self.name_edit)
        form.addRow("", self.cb_pdf)
        v.addLayout(form)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)

    def values(self):
        return self.name_edit.text().strip(), self.cb_pdf.isChecked()

# --- NEW: helpers ---
def _safe_save_character(char, lm):
    try:
        save_character_to_file(char, lm)
    except TypeError:
        save_character_to_file(char)

def _try_export_pdf_from_parsed(parsed_character, name_hint):
    """Export a PDF using the parsed dict (the same object the GUI uses).
    Returns output path on success else None.
    """
    out_dir = os.path.join(os.getcwd(), "characters")
    os.makedirs(out_dir, exist_ok=True)
    out_pdf = os.path.join(out_dir, f"{name_hint}_EP2.pdf")

    # Likely template locations
    template_candidates = [
        os.path.join(os.getcwd(), "Character_Creator", "pdf_conversion", "EP2FormFill.pdf"),
        os.path.join(os.getcwd(), "pdfs", "EP2FormFill.pdf"),
    ]
    template_pdf = None
    for p in template_candidates:
        if os.path.exists(p):
            template_pdf = p
            break

    try:
        import importlib.util
        mod_path = os.path.join(os.getcwd(), "Character_Creator", "pdf_conversion", "fill_ep2_character.py")
        spec = importlib.util.spec_from_file_location("ep2_fill", mod_path)
        if not spec or not spec.loader:
            return None
        ep2_fill = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ep2_fill)

        # Candidate callables
        candidates = []
        for name in ["fill_ep2_character", "export_to_pdf", "fill_character_pdf", "export_character_pdf", "generate_pdf", "main"]:
            fn = getattr(ep2_fill, name, None)
            if callable(fn):
                candidates.append(fn)

        # Try signatures that use the parsed structure
        attempts = []
        attempts.append(((parsed_character,), {}))
        attempts.append(((parsed_character, out_pdf), {}))
        if template_pdf:
            attempts.append(((parsed_character, template_pdf, out_pdf), {}))
            attempts.append(((), {"character": parsed_character, "template_pdf": template_pdf, "out_pdf": out_pdf}))
        attempts.append(((), {"character": parsed_character, "out_pdf": out_pdf}))

        for fn in candidates:
            for args, kwargs in attempts:
                try:
                    fn(*args, **kwargs)
                    if os.path.exists(out_pdf):
                        return out_pdf
                except TypeError:
                    continue
                except Exception:
                    continue
    except Exception:
        pass
    return None

class PoolSpendDialog(QtWidgets.QDialog):
    """Popup to optionally spend pools after seeing a roll (post-roll options)."""
    def __init__(self, character, parent=None, context_label="this test"):
        super().__init__(parent)
        self.setWindowTitle("Modify Outcome?")
        self.setModal(True)
        self.character = character
        self.result = None

        v = QtWidgets.QVBoxLayout(self)
        v.addWidget(QtWidgets.QLabel(f"Modify the outcome of {context_label}? (spend 1 point)"))

        pools = list_pools(character)
        self.cb_plus20 = QtWidgets.QCheckBox("+20 to target (counts as pre-roll)")
        self.cb_reroll = QtWidgets.QCheckBox("Reroll d100")
        self.cb_flip = QtWidgets.QCheckBox("Flip tens/ones")
        self.cb_upgrade = QtWidgets.QCheckBox("Upgrade one tier (success→crit, failure→success)")
        self.cb_negate_crit_fail = QtWidgets.QCheckBox("Negate critical failure (downgrade to normal failure)")

        for cb in [self.cb_plus20, self.cb_reroll, self.cb_flip, self.cb_upgrade, self.cb_negate_crit_fail]:
            v.addWidget(cb)

        # Pool selection (radio)
        self.pool_group = QtWidgets.QButtonGroup(self)
        pool_row = QtWidgets.QHBoxLayout()
        pool_row.addWidget(QtWidgets.QLabel("Pay with:"))
        self.rb_insight = QtWidgets.QRadioButton(f"Insight ({pools.get('Insight',0)})")
        self.rb_moxie = QtWidgets.QRadioButton(f"Moxie ({pools.get('Moxie',0)})")
        self.rb_vigor = QtWidgets.QRadioButton(f"Vigor ({pools.get('Vigor',0)})")
        self.rb_flex = QtWidgets.QRadioButton(f"Flex ({pools.get('Flex',0)})")
        for rb in [self.rb_insight, self.rb_moxie, self.rb_vigor, self.rb_flex]:
            self.pool_group.addButton(rb)
            pool_row.addWidget(rb)
        v.addLayout(pool_row)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        v.addWidget(btns)

    def get_selection(self):
        # Determine which pool was selected
        pool_name = None
        if self.rb_insight.isChecked(): pool_name = "Insight"
        elif self.rb_moxie.isChecked(): pool_name = "Moxie"
        elif self.rb_vigor.isChecked(): pool_name = "Vigor"
        elif self.rb_flex.isChecked(): pool_name = "Flex"

        actions = {
            "plus20": self.cb_plus20.isChecked(),
            "reroll": self.cb_reroll.isChecked(),
            "flip": self.cb_flip.isChecked(),
            "upgrade": self.cb_upgrade.isChecked(),
            "neg_crit_fail": self.cb_negate_crit_fail.isChecked(),
        }
        if any(actions.values()) and pool_name:
            return pool_name, actions
        return None, actions

class EP2eGUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eclipse Phase 2e — Offline Session Tracker")
        self.setGeometry(100, 100, 1100, 760)

        self.character = None
        self.current_file = None

        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)

        # Overview
        self.overview_text = QtWidgets.QTextEdit()
        self.overview_text.setReadOnly(True)
        self.tabs.addTab(self.overview_text, "Overview")

        # Skill Rolls
        self.skill_tab = QtWidgets.QWidget(); self._init_skill_tab()
        self.tabs.addTab(self.skill_tab, "Skill Rolls")

        # Stress Tests
        self.stress_tab = QtWidgets.QWidget(); self._init_stress_tab()
        self.tabs.addTab(self.stress_tab, "Stress Tests")

        # Remorphing
        self.remorph_tab = QtWidgets.QWidget(); self._init_remorph_tab()
        self.tabs.addTab(self.remorph_tab, "Remorphing")

        # Combat
        self.combat_tab = QtWidgets.QWidget(); self._init_combat_tab()
        self.tabs.addTab(self.combat_tab, "Combat (Basic)")

        # Log
        self.log_text = QtWidgets.QTextEdit(); self.log_text.setReadOnly(True)
        self.tabs.addTab(self.log_text, "Session Log")

        # Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        load_action = QtWidgets.QAction("Load Character…", self); load_action.triggered.connect(self.load_character)
        save_action = QtWidgets.QAction("Save Session As…", self); save_action.triggered.connect(self.save_session_as)
        # NEW
        gen_action = QtWidgets.QAction("Generate Random Character…", self); gen_action.triggered.connect(self.generate_random_character_action)
        file_menu.addAction(gen_action)
        file_menu.addAction(load_action); file_menu.addAction(save_action)

        self.statusBar().showMessage("Ready")

    # ---------- UI Builders ----------
    def _init_skill_tab(self):
        L = QtWidgets.QVBoxLayout(); self.skill_tab.setLayout(L)
        row = QtWidgets.QHBoxLayout(); L.addLayout(row)
        self.skill_select = QtWidgets.QComboBox(); row.addWidget(QtWidgets.QLabel("Skill:")); row.addWidget(self.skill_select,1)
        self.mod_input = QtWidgets.QSpinBox(); self.mod_input.setRange(-90,90); row.addWidget(QtWidgets.QLabel("Modifier:")); row.addWidget(self.mod_input)
        self.roll_skill_btn = QtWidgets.QPushButton("Roll Skill"); row.addWidget(self.roll_skill_btn)
        self.roll_skill_btn.clicked.connect(self.roll_skill)
        self.skill_result = QtWidgets.QTextEdit(); self.skill_result.setReadOnly(True); L.addWidget(self.skill_result)

    def _init_stress_tab(self):
        L = QtWidgets.QVBoxLayout(); self.stress_tab.setLayout(L)
        row = QtWidgets.QHBoxLayout(); L.addLayout(row)
        self.stress_amount = QtWidgets.QSpinBox(); self.stress_amount.setRange(1,100); self.stress_amount.setValue(1)
        self.stress_btn = QtWidgets.QPushButton("Apply Stress & Roll WIL×3")
        row.addWidget(QtWidgets.QLabel("Stress damage:")); row.addWidget(self.stress_amount); row.addWidget(self.stress_btn)
        self.stress_btn.clicked.connect(self.apply_stress_roll)
        self.stress_result = QtWidgets.QTextEdit(); self.stress_result.setReadOnly(True); L.addWidget(self.stress_result)

    def _init_remorph_tab(self):
        L = QtWidgets.QVBoxLayout(); self.remorph_tab.setLayout(L)
        row = QtWidgets.QHBoxLayout(); L.addLayout(row)
        self.remorph_type = QtWidgets.QComboBox(); self.remorph_type.addItems(["Integration","Alienation","Continuity"])
        self.remorph_btn = QtWidgets.QPushButton("Roll Remorphing Test")
        row.addWidget(QtWidgets.QLabel("Test:")); row.addWidget(self.remorph_type); row.addWidget(self.remorph_btn)
        self.remorph_btn.clicked.connect(self.roll_remorph)
        self.remorph_result = QtWidgets.QTextEdit(); self.remorph_result.setReadOnly(True); L.addWidget(self.remorph_result)

    def _init_combat_tab(self):
        L = QtWidgets.QVBoxLayout(); self.combat_tab.setLayout(L)
        # Attack inputs
        atk_row = QtWidgets.QHBoxLayout(); L.addLayout(atk_row)
        self.cb_melee = QtWidgets.QRadioButton("Melee"); self.cb_ranged = QtWidgets.QRadioButton("Ranged"); self.cb_ranged.setChecked(True)
        atk_row.addWidget(self.cb_ranged); atk_row.addWidget(self.cb_melee)
        self.skill_attack = QtWidgets.QComboBox(); atk_row.addWidget(QtWidgets.QLabel("Attack skill:")); atk_row.addWidget(self.skill_attack,1)

        mod_row = QtWidgets.QHBoxLayout(); L.addLayout(mod_row)
        self.spin_atk_mod = QtWidgets.QSpinBox(); self.spin_atk_mod.setRange(-90,90)
        self.chk_aim = QtWidgets.QCheckBox("Aim (+10)"); self.chk_cover = QtWidgets.QCheckBox("Target in Cover (−10)")
        self.fire_mode = QtWidgets.QButtonGroup(self)
        rb_single = QtWidgets.QRadioButton("Single"); rb_burst = QtWidgets.QRadioButton("Burst (−10)"); rb_auto = QtWidgets.QRadioButton("Full Auto (−20)")
        rb_single.setChecked(True)
        self.fire_mode.addButton(rb_single,1); self.fire_mode.addButton(rb_burst,2); self.fire_mode.addButton(rb_auto,3)
        for w in [QtWidgets.QLabel("Atk Mod:"), self.spin_atk_mod, self.chk_aim, self.chk_cover, rb_single, rb_burst, rb_auto]:
            mod_row.addWidget(w)

        # Defense inputs
        def_row = QtWidgets.QHBoxLayout(); L.addLayout(def_row)
        self.chk_defend = QtWidgets.QCheckBox("Defender Reacts")
        self.def_skill = QtWidgets.QComboBox()
        self.spin_def_mod = QtWidgets.QSpinBox(); self.spin_def_mod.setRange(-90,90)
        for w in [self.chk_defend, QtWidgets.QLabel("Defense skill:"), self.def_skill, QtWidgets.QLabel("Def Mod:"), self.spin_def_mod]:
            def_row.addWidget(w)

        # Damage & armor
        dmg_row = QtWidgets.QHBoxLayout(); L.addLayout(dmg_row)
        self.spin_dv = QtWidgets.QSpinBox(); self.spin_dv.setRange(0,200); self.spin_dv.setValue(10)
        self.spin_armor = QtWidgets.QSpinBox(); self.spin_armor.setRange(0,50)
        self.spin_ap = QtWidgets.QSpinBox(); self.spin_ap.setRange(0,50)
        for w in [QtWidgets.QLabel("Base DV:"), self.spin_dv, QtWidgets.QLabel("Target Armor:"), self.spin_armor, QtWidgets.QLabel("AP:"), self.spin_ap]:
            dmg_row.addWidget(w)

        # Buttons
        btn_row = QtWidgets.QHBoxLayout(); L.addLayout(btn_row)
        self.btn_attack = QtWidgets.QPushButton("Resolve Attack"); btn_row.addWidget(self.btn_attack)
        self.btn_attack.clicked.connect(self.resolve_attack)

        self.combat_log = QtWidgets.QTextEdit(); self.combat_log.setReadOnly(True); L.addWidget(self.combat_log)

    # ---------- File ops ----------
    def load_character(self):
        start_dir = os.path.join(os.getcwd(), "characters")
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Character", start_dir, "Text Files (*.txt)")
        if not path: return
        self.character = parse_character_txt(path)
        self.current_file = path
        self.refresh_overview()
        self.populate_skills()
        self.log(f"Loaded character from {path}")

    def save_session_as(self):
        if not self.character:
            QtWidgets.QMessageBox.warning(self, "No character", "Load a character first."); return
        base = os.path.splitext(os.path.basename(self.current_file or "character.txt"))[0]
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        default_name = f"{base}_session_{ts}.txt"
        start_dir = os.path.join(os.getcwd(), "characters"); os.makedirs(start_dir, exist_ok=True)
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Session As", os.path.join(start_dir, default_name), "Text Files (*.txt)")
        if not path: return
        txt = serialize_character_txt(self.character)
        with open(path, "w", encoding="utf-8") as f: f.write(txt)
        self.log(f"Session saved to {path}")
        QtWidgets.QMessageBox.information(self, "Saved", f"Session saved:\n{path}")

    # ---------- NEW: Generate + optional PDF ----------
    def generate_random_character_action(self):
        dlg = GenerateDialog(self)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        name, want_pdf = dlg.values()
        if not name:
            return
        try:
            lm = LibraryManager()
            lm.load_all_libraries()
            char = generate_random_character(name, lm)
            _safe_save_character(char, lm)

            # Load into GUI immediately (parsed representation)
            path = os.path.join(os.getcwd(), "characters", f"{name}.txt")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Expected character file not found: {path}")
            self.character = parse_character_txt(path)
            self.current_file = path
            self.refresh_overview()
            self.populate_skills()

            # Optional PDF using the parsed dict to match your existing filler expectations
            if want_pdf:
                pdf_out = _try_export_pdf_from_parsed(self.character, name)
                if pdf_out:
                    QtWidgets.QMessageBox.information(self, "Generated", f"Character '{name}' generated and loaded.\nPDF exported:\n{pdf_out}")
                else:
                    QtWidgets.QMessageBox.warning(self, "Generated (PDF failed)", f"Character '{name}' generated and loaded, but PDF export did not complete. Check fill_ep2_character.py.")
            else:
                QtWidgets.QMessageBox.information(self, "Generated", f"Character '{name}' generated and loaded.")
            self.log(f"Generated character '{name}'")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Generation Failed", f"{type(e).__name__}: {e}")

    # ---------- Helpers ----------
    def refresh_overview(self):
        if not self.character: self.overview_text.clear(); return
        parts = []
        parts.append("Aptitudes:"); [parts.append(f"  {k}: {v}") for k,v in self.character["Aptitudes"].items()]
        parts.append("\nSkills:");   [parts.append(f"  {k}: {self.character['Skills'][k]}") for k in sorted(self.character["Skills"].keys())]
        parts.append("\nOther Stats:"); [parts.append(f"  {k}: {v}") for k,v in self.character["Other Stats"].items()]
        self.overview_text.setPlainText("\n".join(parts))

    def populate_skills(self):
        self.skill_select.clear(); self.def_skill.clear(); self.skill_attack.clear()
        if not self.character: return
        skills = sorted(self.character["Skills"].keys())
        self.skill_select.addItems(skills)
        self.def_skill.addItems(skills + ["Fray"] if "Fray" not in skills else skills)
        self.skill_attack.addItems(skills)

    def log(self, msg): self.log_text.append(msg)

    def prompt_pool_spend(self, context_label):
        dlg = PoolSpendDialog(self.character, self, context_label)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            pool_name, actions = dlg.get_selection()
            if pool_name and any(actions.values()) and spend_pool(self.character, pool_name, 1):
                self.refresh_overview()
                return pool_name, actions
        return None, {"plus20":False,"reroll":False,"flip":False,"upgrade":False,"neg_crit_fail":False}

    # ---------- Rolls ----------
    def roll_skill(self):
        if not self.character:
            QtWidgets.QMessageBox.warning(self, "No character", "Load a character first."); return
        skill = self.skill_select.currentText()
        base = self.character["Skills"].get(skill, 0)
        mod = self.mod_input.value()
        pool_used, actions = self.prompt_pool_spend(f"Skill: {skill}")
        if actions["plus20"]:
            mod += 20
        tens, ones, roll_val = roll_d100()
        target = max(0, min(99, base + mod))
        if actions["flip"]:
            roll_val = int(f"{ones}{tens}")
        if actions["reroll"]:
            tens, ones, roll_val = roll_d100()
        out = evaluate_roll(roll_val, target)
        if actions["neg_crit_fail"] and out["tier"] == "critical_failure":
            out["tier"] = "failure"; out["label"] = "FAILURE"
        if actions["upgrade"]:
            order = ["critical_failure","failure","success","critical_success"]
            i = max(0, order.index(out["tier"])); i = min(len(order)-1, i+1)
            new = order[i]
            out["tier"] = new; out["label"] = {"critical_success":"CRITICAL SUCCESS","success":"SUCCESS","failure":"FAILURE","critical_failure":"CRITICAL FAILURE"}[new]

        display = fmt_roll_for_display(roll_val//10, roll_val%10)
        summaries = {
            "critical_success": "Exceptional result — task completed better/faster than expected.",
            "success": "Task completed as intended.",
            "failure": "Task failed — no progress or flawed result.",
            "critical_failure": "Severe error — things get worse or a complication occurs.",
        }
        summary = summaries[out["tier"]]
        line = f"{skill} | Target {target} | Roll {display} → {out['label']} — {summary}"
        self.skill_result.append(line); self.log(line)

    def apply_stress_roll(self):
        if not self.character:
            QtWidgets.QMessageBox.warning(self, "No character", "Load a character first."); return
        stress = self.stress_amount.value()
        apt = self.character["Aptitudes"].get("WIL", 0)
        mod = 0
        pool_used, actions = self.prompt_pool_spend("Stress Test (WIL×3)")
        if actions["plus20"]:
            mod += 20
        tens, ones, roll_val = roll_d100()
        target = max(0, min(99, apt * 3 + mod))
        if actions["flip"]:
            roll_val = int(f"{ones}{tens}")
        if actions["reroll"]:
            tens, ones, roll_val = roll_d100()
        out = evaluate_roll(roll_val, target)
        if actions["neg_crit_fail"] and out["tier"] == "critical_failure":
            out["tier"] = "failure"; out["label"] = "FAILURE"
        if actions["upgrade"]:
            order = ["critical_failure","failure","success","critical_success"]
            i = max(0, order.index(out["tier"])); i = min(len(order)-1, i+1)
            new = order[i]; out["tier"]=new; out["label"]={"critical_success":"CRITICAL SUCCESS","success":"SUCCESS","failure":"FAILURE","critical_failure":"CRITICAL FAILURE"}[new]

        updated, trauma = apply_stress_and_trauma(self.character, stress, out)
        self.character = updated; self.refresh_overview()
        display = fmt_roll_for_display(roll_val//10, roll_val%10)
        summary = stress_outcome_summary(out, stress, self.character, trauma_text=trauma)
        line = f"Stress Test WIL×3={target} | Roll {display} → {out['label']} — {summary}"
        self.stress_result.append(line); self.log(line)

    def roll_remorph(self):
        if not self.character:
            QtWidgets.QMessageBox.warning(self, "No character", "Load a character first."); return
        test = self.remorph_type.currentText()
        mod = 0
        pool_used, actions = self.prompt_pool_spend(f"{test} Test")
        if actions["plus20"]:
            mod += 20
        tens, ones, roll_val = roll_d100()
        apt = self.character["Aptitudes"]
        if test == "Integration":
            target = max(0, min(99, apt.get("SOM",0)*3 + mod))
        else:
            target = max(0, min(99, apt.get("WIL",0)*3 + mod))
        if actions["flip"]:
            roll_val = int(f"{ones}{tens}")
        if actions["reroll"]:
            tens, ones, roll_val = roll_d100()
        out = evaluate_roll(roll_val, target)
        if actions["neg_crit_fail"] and out["tier"] == "critical_failure":
            out["tier"] = "failure"; out["label"] = "FAILURE"
        if actions["upgrade"]:
            order = ["critical_failure","failure","success","critical_success"]
            i = max(0, order.index(out["tier"])); i = min(len(order)-1, i+1)
            new = order[i]; out["tier"]=new; out["label"]={"critical_success":"CRITICAL SUCCESS","success":"SUCCESS","failure":"FAILURE","critical_failure":"CRITICAL FAILURE"}[new]

        summary = remorph_outcome_summary(test, {"target":target, "outcome":out})
        display = fmt_roll_for_display(roll_val//10, roll_val%10)
        line = f"{test} | Target {target} | Roll {display} → {out['label']} — {summary}"
        self.remorph_result.append(line); self.log(line)

    # ---------- Combat ----------
    def resolve_attack(self):
        if not self.character:
            QtWidgets.QMessageBox.warning(self, "No character", "Load a character first."); return
        atk_skill_name = self.skill_attack.currentText()
        atk_base = self.character["Skills"].get(atk_skill_name, 0)
        atk_mod = self.spin_atk_mod.value()
        if self.chk_aim.isChecked(): atk_mod += 10
        if self.chk_cover.isChecked(): atk_mod -= 10
        mode_id = self.fire_mode.checkedId()
        if mode_id == 2: atk_mod -= 10
        elif mode_id == 3: atk_mod -= 20

        pool_used, actions = self.prompt_pool_spend(f"Attack: {atk_skill_name}")
        if actions["plus20"]:
            atk_mod += 20

        t_tens, t_ones, t_val = roll_d100()
        if actions["flip"]:
            t_val = int(f"{t_ones}{t_tens}")
        if actions["reroll"]:
            t_tens, t_ones, t_val = roll_d100()
        atk_target = max(0, min(99, atk_base + atk_mod))
        att_out = evaluate_roll(t_val, atk_target)
        if actions["neg_crit_fail"] and att_out["tier"] == "critical_failure":
            att_out["tier"] = "failure"; att_out["label"] = "FAILURE"
        if actions["upgrade"]:
            order = ["critical_failure","failure","success","critical_success"]
            i = max(0, order.index(att_out["tier"])); i = min(len(order)-1, i+1)
            new = order[i]; att_out["tier"]=new; att_out["label"]={"critical_success":"CRITICAL SUCCESS","success":"SUCCESS","failure":"FAILURE","critical_failure":"CRITICAL FAILURE"}[new]

        defended = False; def_out = None; def_line = ""
        if self.chk_defend.isChecked():
            def_skill_name = self.def_skill.currentText()
            def_base = self.character["Skills"].get(def_skill_name, 0)
            def_mod = self.spin_def_mod.value()
            d_tens, d_ones, d_val = roll_d100()
            def_target = max(0, min(99, def_base + def_mod))
            def_out = evaluate_roll(d_val, def_target)
            defended = (def_out["success"] and (not att_out["success"] or d_val <= def_target and d_val > t_val))
            def_line = f" | Defense {def_skill_name} T{def_target} Roll {d_val//10}{d_val%10} → {def_out['label']}"

        line = f"Attack {atk_skill_name} T{atk_target} Roll {t_val//10}{t_val%10} → {att_out['label']}"
        if def_line: line += def_line
        if att_out["success"] and not defended:
            base_dv = self.spin_dv.value()
            armor = self.spin_armor.value()
            ap = self.spin_ap.value()
            after = apply_damage_after_armor(base_dv, armor, ap)
            state = apply_damage_to_character(self.character, after)
            self.refresh_overview()
            line += f" | HIT for {after} after armor → Total {state['total_damage']}, Wounds {state['wounds']} ({state['state']})"
        else:
            line += " | MISS"
        self.combat_log.append(line); self.log(line)

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = EP2eGUI(); w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
