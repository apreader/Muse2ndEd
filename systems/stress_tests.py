import random
from .roll_core import evaluate_roll

# Generic trauma effects list (editable).
# Replace/extend with official EP2e trauma outcomes if you want exact text.
TRAUMA_EFFECTS = [
    "panic and lose your next action",
    "shaken; −10 to actions for the scene",
    "distracted; you can only take simple actions for 1d10 minutes",
    "fear response; you must flee or take cover for 1d10 rounds",
    "dissociation; −30 to social tests for 1d10 minutes",
    "tunnel vision; −20 to Perceive for 1d10 minutes",
    "stunned; skip your next turn",
    "obsessive focus; you fixate on the stressor for 1d10 minutes",
    "nausea; −10 to physical actions for 1d10 minutes",
    "freeze; cannot act for 1 round",
]

def _to_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default

def roll_d10():
    return random.randint(1, 10)

def apply_stress_and_trauma(character: dict, stress_amount: int, outcome: dict):
    """Apply stress per event and check trauma.
    EP-friendly approach:
      - Add stress_amount to Other Stats['Stress Taken'].
      - If roll outcome is failure/critical_failure AND the single event stress_amount >= Trauma Threshold,
        apply ONE trauma.
    Returns (updated_character, trauma_text or None).
    """
    other = character.setdefault("Other Stats", {})
    taken = _to_int(other.get("Stress Taken", 0))
    thresh = _to_int(other.get("Trauma Threshold", 0))

    taken += int(stress_amount)
    other["Stress Taken"] = taken

    trauma_text = None
    if outcome["tier"] in ("failure", "critical_failure") and thresh > 0 and stress_amount >= thresh:
        # Apply one trauma
        other["Traumas Taken"] = _to_int(other.get("Traumas Taken", 0)) + 1
        raw = random.choice(TRAUMA_EFFECTS)
        # Replace any 1d10 with an actual roll
        trauma_text = raw.replace("1d10", str(roll_d10()))

        # Keep last trauma description for reference
        other["Last Trauma"] = trauma_text

    return character, trauma_text

def stress_outcome_summary(outcome, stress_amount, character, trauma_text=None):
    """Return one-sentence generic result text; include trauma if it happened."""
    tier = outcome["tier"]
    if tier == "critical_success":
        base = "You steel your mind; take the stress with composure (no extra effects)."
    elif tier == "success":
        base = "You keep it together; stress applies but no trauma is triggered."
    elif tier == "failure":
        base = "You falter; stress applies."
    else:
        base = "You crack under pressure; stress hits hard."

    if trauma_text:
        return f"{base} You suffer a trauma: {trauma_text}."
    return base
