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


def short_brief_prompt(*args):
    texts = "\n".join(f"{i + 1}. {text}" for i, text in enumerate(args))
    return f"""
Вот пункты, которые я собрал для составления брифа:

{texts}

На основе этого сделай только краткий бриф в следующем формате,
без исходных текстов и лишних комментариев — просто заполни шаблон:

📍 Ниша: 
🎯 Цель:
🧩 Смыслы: 
📹 Форматы:
💼 Продукты: 
"""
