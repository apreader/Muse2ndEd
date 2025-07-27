import random
from collections import defaultdict

# Standard rep networks
REP_NETWORKS = ["c-rep", "e-rep", "f-rep", "g-rep", "i-rep", "r-rep", "x-rep"]

# Rep preference weights by faction
FACTION_REP_WEIGHTS = {
    "hypercorp": {"c-rep": 4, "f-rep": 2, "i-rep": 2},
    "anarchist": {"g-rep": 5, "x-rep": 3, "i-rep": 2},
    "extropian": {"c-rep": 3, "g-rep": 3, "f-rep": 2},
    "titanians": {"c-rep": 4, "i-rep": 3, "e-rep": 2},
    "moravec": {"x-rep": 4, "i-rep": 3, "g-rep": 2},
    "brinker": {"r-rep": 4, "g-rep": 3, "x-rep": 2},
    "scum": {"f-rep": 4, "g-rep": 3, "c-rep": 2},
    "jovian": {"c-rep": 5, "r-rep": 2, "f-rep": 1},
    "academic": {"i-rep": 5, "e-rep": 2, "x-rep": 1},
}

# Rep influence modifiers for backgrounds
BACKGROUND_REP_BONUSES = {
    "civilian": {"c-rep": 3, "f-rep": 2},
    "uplift": {"e-rep": 2, "x-rep": 3},
    "technician": {"i-rep": 4},
    "scientist": {"i-rep": 5},
    "criminal": {"g-rep": 5},
    "military": {"c-rep": 3, "r-rep": 2},
    "colonist": {"r-rep": 4, "e-rep": 2},
}

# Career influence on reputation
CAREER_REP_BONUSES = {
    "reporter": {"f-rep": 4},
    "smuggler": {"g-rep": 3, "x-rep": 2},
    "gatecrasher": {"x-rep": 5},
    "cop": {"c-rep": 4},
    "researcher": {"i-rep": 4},
    "ecologist": {"e-rep": 4},
}

# Interest tags influencing rep
INTEREST_REP_TAGS = {
    "green politics": {"e-rep": 2},
    "gate travel": {"x-rep": 2},
    "celebrity": {"f-rep": 3},
    "black market": {"g-rep": 2},
    "reclaiming Earth": {"r-rep": 2},
}

def normalize_weights(weight_dict):
    total_weight = sum(weight_dict.values())
    if total_weight == 0:
        return {k: 0 for k in weight_dict}
    return {k: v / total_weight for k, v in weight_dict.items()}

def distribute_rep(normalized_weights, total_points=100, max_per_network=80):
    rep = defaultdict(int)
    points_left = total_points
    weight_items = list(normalized_weights.items())

    # Sort by weight to prioritize higher-weighted networks
    weight_items.sort(key=lambda x: x[1], reverse=True)

    for network, weight in weight_items:
        if points_left <= 0:
            break
        allocation = min(int(weight * total_points), max_per_network, points_left)
        rep[network] += allocation
        points_left -= allocation

    # Distribute leftovers randomly among allowed networks
    if points_left > 0:
        available = [net for net in REP_NETWORKS if rep[net] < max_per_network]
        while points_left > 0 and available:
            net = random.choice(available)
            rep[net] += 1
            points_left -= 1
            if rep[net] >= max_per_network:
                available.remove(net)

    return dict(rep)

def redistribute_reputation(rep_dict, min_rep=10):
    # Collect all reps below minimum threshold
    low_reps = {k: v for k, v in rep_dict.items() if v < min_rep}
    high_reps = {k: v for k, v in rep_dict.items() if v >= min_rep}

    points_to_redistribute = sum(low_reps.values())

    # Zero out low reps
    for k in low_reps:
        rep_dict[k] = 0

    if not high_reps:
        # If all reps are low, distribute points evenly
        count = len(rep_dict)
        base = points_to_redistribute // count
        remainder = points_to_redistribute % count
        for k in rep_dict:
            rep_dict[k] = base + (1 if remainder > 0 else 0)
            remainder -= 1
        return rep_dict

    # Sort high reps ascending (lowest first) for redistribution priority
    sorted_high = sorted(high_reps.items(), key=lambda x: x[1])

    # Redistribute points 1 by 1 to lowest reps
    while points_to_redistribute > 0:
        for i, (k, val) in enumerate(sorted_high):
            if points_to_redistribute <= 0:
                break
            rep_dict[k] += 1
            points_to_redistribute -= 1
            sorted_high[i] = (k, rep_dict[k])
        # Re-sort after distributing to keep lowest first
        sorted_high.sort(key=lambda x: x[1])

    return rep_dict

def generate_reputation(faction, background, career=None, interests=None, is_uplift=False):
    weights = defaultdict(int)

    # Faction-based weights (primary)
    faction_weights = FACTION_REP_WEIGHTS.get(faction.lower(), {})
    for net, val in faction_weights.items():
        weights[net] += val * 2  # faction is weighted most

    # Background influence
    bg_weights = BACKGROUND_REP_BONUSES.get(background.lower(), {})
    for net, val in bg_weights.items():
        weights[net] += val

    # Career influence
    if career:
        career_weights = CAREER_REP_BONUSES.get(career.lower(), {})
        for net, val in career_weights.items():
            weights[net] += val

    # Interest tags
    if interests:
        for tag in interests:
            tag_weights = INTEREST_REP_TAGS.get(tag.lower(), {})
            for net, val in tag_weights.items():
                weights[net] += val

    # Uplift bonus
    if is_uplift:
        weights["x-rep"] += 2
        weights["e-rep"] += 1

    normalized = normalize_weights(weights)
    rep = distribute_rep(normalized)

    # Redistribute rep so no network is below 10
    rep = redistribute_reputation(rep, min_rep=10)

    return rep

# Example usage:
if __name__ == "__main__":
    rep = generate_reputation(
        faction="Anarchist",
        background="Uplift",
        career="Gatecrasher",
        interests=["green politics", "gate travel"],
        is_uplift=True
    )
    for k, v in rep.items():
        print(f"{k}: {v}")
