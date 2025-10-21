language_map = {
    "ru": "на русском языке",
    "eu": "на английском языке",
}

type_prompts = {
    "story_or_insight": "Создай историю или инсайт",
    "selling_reels": "Создай продающий reels",
    "trust_me": "Создай доверительный пост",
}


def alcove_prompt(*args):
    texts = "\n".join(f"{i + 1}. {text}" for i, text in enumerate(args))
    return f"""
{texts}

Кратко опиши и объедини всё это в одну тему.
"""
