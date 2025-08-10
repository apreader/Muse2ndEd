def resolve_placeholder_skills(raw_skills, choice_skills):
    """
    raw_skills: dict with skill names (some placeholders) -> rating
    choice_skills: list of dicts parsed from Notes with keys:
        SkillCategory, Rating, CommonFields

    Returns: new dict with placeholders replaced by resolved skill names.
    """

    choice_cache = {}  # (category.lower(), rating) -> chosen common field

    updated_skills = {}

    for skill_name, rating in raw_skills.items():
        if "Choice" in skill_name:
            parts = skill_name.split()
            if len(parts) == 3 and parts[1] == "Choice":
                category = parts[0]
                rating_num = int(parts[2])
                key = (category.lower(), rating_num)

                if key not in choice_cache:
                    # Find matching choice skill and pick a random field
                    for choice in choice_skills:
                        if choice["SkillCategory"].lower() == category.lower() and choice["Rating"] == rating_num:
                            choice_cache[key] = random.choice(choice["CommonFields"])
                            break
                    else:
                        # No matching choice skill found, fallback to original key
                        choice_cache[key] = None

                chosen_field = choice_cache[key]
                if chosen_field:
                    display_cat = "Knowledge" if category.lower() == "know" else category
                    resolved_name = f"{display_cat} ({chosen_field})"
                else:
                    resolved_name = skill_name
            else:
                resolved_name = skill_name
        else:
            resolved_name = skill_name

        # Merge ratings if skill repeats
        if resolved_name in updated_skills:
            updated_skills[resolved_name] = max(rating, updated_skills[resolved_name])
        else:
            updated_skills[resolved_name] = rating

    return updated_skills
