import random

def roll_d100():
    """Return (tens, ones, total) where total is 0..99 using two d10s (0-9)."""
    tens = random.randint(0, 9)
    ones = random.randint(0, 9)
    total = tens * 10 + ones  # 00 == 0
    return tens, ones, total

def make_total(tens, ones):
    return tens * 10 + ones

def fmt_roll_for_display(tens, ones):
    return f"{tens}{ones}"  # "00", "13", "99"

def evaluate_roll(roll_value, target):
    """Evaluate against EP2e rules.
    - Success if roll <= target
    - Critical if doubles (00,11,22,...,99). 00 is always critical success; 99 is always critical failure.
    - Superior results: on success, <=33 -> 2 superiors; <=66 -> 1 superior.
    Returns a dict with fields: success, critical, superiors, label, tier
    """
    success = roll_value <= target
    tens = roll_value // 10
    ones = roll_value % 10
    is_doubles = (tens == ones)

    if is_doubles:
        if roll_value == 0:
            tier = "critical_success"
        elif roll_value == 99:
            tier = "critical_failure"
        else:
            tier = "critical_success" if success else "critical_failure"
    else:
        tier = "success" if success else "failure"

    superiors = 0
    if success:
        if roll_value <= 33:
            superiors = 2
        elif roll_value <= 66:
            superiors = 1

    label_map = {
        "critical_success": "CRITICAL SUCCESS",
        "success": "SUCCESS",
        "failure": "FAILURE",
        "critical_failure": "CRITICAL FAILURE",
    }

    return {
        "success": success,
        "critical": (tier.startswith("critical")),
        "superiors": superiors,
        "tier": tier,
        "label": label_map[tier],
        "roll": roll_value,
        "target": target,
    }
