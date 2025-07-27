import random

def select_languages(aptitudes):
    language_pool = [
        "Arabic", "Cantonese", "English", "French", "Hindi",
        "Japanese", "Mandarin", "Portuguese", "Russian", "Skandinavíska", "Spanish"
    ]

    known_languages = {"English"}
    known_languages.add(random.choice([lang for lang in language_pool if lang != "English"]))

    cog_int = aptitudes.get("COG", 0) + aptitudes.get("INT", 0)

    if cog_int >= 45:
        known_languages.update(random.sample(
            [lang for lang in language_pool if lang not in known_languages], 2
        ))
    elif cog_int >= 35:
        known_languages.add(random.choice(
            [lang for lang in language_pool if lang not in known_languages]
        ))

    return list(known_languages)
