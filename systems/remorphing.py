import random
from .roll_core import evaluate_roll

def remorph_roll(character: dict, test_type: str, roll_value: int = None):
    """Compute target and evaluate outcome for Integration/Alienation/Continuity.
    Targets:
      Integration: SOM × 3
      Alienation: WIL × 3
      Continuity: WIL × 3
    """
    apt = character.get("Aptitudes", {})
    if test_type == "Integration":
        target = max(0, min(99, int(apt.get("SOM", 0)) * 3))
    elif test_type == "Alienation":
        target = max(0, min(99, int(apt.get("WIL", 0)) * 3))
    else:  # Continuity
        target = max(0, min(99, int(apt.get("WIL", 0)) * 3))

    if roll_value is None:
        raise ValueError("roll_value must be provided by caller.")
    out = evaluate_roll(roll_value, target)
    return {"target": target, "outcome": out}

def remorph_outcome_summary(test_type: str, result: dict):
    roll_hours = random.randint(1, 10)
    roll_minutes = random.randint(1, 10)
    tier = result["outcome"]["tier"]
    if test_type == "Integration":
        if tier in ("success","critical_success"):
            return "You adjust to the morph smoothly."
        else:
            return f"You struggle to sync with the morph; −10 to all actions for {roll_hours} hours."
    elif test_type == "Alienation":
        if tier in ("success","critical_success"):
            return "Your self-image aligns with the morph."
        else:
            return "You feel disconnected from the morph; −10 to all actions until you adapt."
    else:  # Continuity
        if tier in ("success","critical_success"):
            return "Continuity maintained; you orient quickly."
        else:
            return f"Identity dissonance hits; −30 to all actions for {roll_minutes} minutes."
