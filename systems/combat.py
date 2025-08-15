import math
from .roll_core import evaluate_roll

def clamp_target(x):
    return max(0, min(99, int(x)))

def build_attack_target(skill_value: int, modifiers: int = 0):
    return clamp_target(skill_value + modifiers)

def resolve_attack_vs_defense(att_roll: int, att_target: int, def_roll: int = None, def_target: int = None):
    """Return dict with attack_outcome, defended(bool). Opposed if defense provided."""
    att_out = evaluate_roll(att_roll, att_target)
    defended = False
    if def_roll is not None and def_target is not None:
        def_out = evaluate_roll(def_roll, def_target)
        if def_out["success"] and (not att_out["success"] or def_roll <= def_target and def_roll > att_roll):
            defended = True
    return {"attack": att_out, "defended": defended}

def apply_damage_after_armor(base_damage: int, armor: int, ap: int = 0):
    effective_armor = max(0, armor - max(0, ap))
    return max(0, int(base_damage) - effective_armor)

def apply_damage_to_character(character: dict, dmg: int):
    other = character.setdefault("Other Stats", {})
    dur = int(other.get("Durability", 0))
    wt = int(other.get("Wound Threshold", 0))
    dr = int(other.get("Death Rating", 0))

    taken = int(other.get("Damage Taken", 0)) + int(dmg)
    wounds = int(other.get("Wounds Taken", 0))

    # Wounds: each time a single hit >= WT, +1 wound (may accumulate if large hits - simplified: floor(hit/WT))
    if wt > 0 and dmg >= wt:
        wounds += max(1, dmg // wt)

    other["Damage Taken"] = taken
    other["Wounds Taken"] = wounds

    state = "OK"
    if dr and taken >= dr:
        state = "DEAD/TERMINATED"
    elif dur and taken >= dur:
        state = "UNCONSCIOUS/INCAPPED"

    return {"damage_after_armor": dmg, "total_damage": taken, "wounds": wounds, "state": state}
