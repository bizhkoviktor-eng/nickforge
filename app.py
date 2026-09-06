from flask import Flask, render_template, request, jsonify
import random
import re

app = Flask(__name__)

PREFIXES = {
    "dark": [
        "Void", "Shadow", "Night", "Grim", "Dark",
        "Phantom", "Raven", "Abyss", "Ghost"
    ],
    "cool": [
        "Nova", "Vex", "Zyn", "Neo", "Flux",
        "Zen", "Axel", "Frost", "Blaze"
    ],
    "funny": [
        "Potato", "Pickle", "Goofy", "Waffle", "Bongo",
        "Noodle", "Chonky", "Bonk", "Muffin"
    ],
    "pro": [
        "Clutch", "Fury", "Prime", "Aim", "Rush",
        "Elite", "Ace", "Sharp", "Peak"
    ],
    "cyber": [
        "Cyber", "Byte", "Glitch", "Pixel", "Neon",
        "Zero", "Hex", "Code", "Syn"
    ],
    "fantasy": [
        "Drake", "Elder", "Mystic", "Rune", "Fae",
        "Dragon", "Storm", "Ember", "Moon"
    ]
}

SUFFIXES = {
    "dark": [
        "X", "666", "Shade", "Reaper",
        "Soul", "Wraith", "Born", "Core"
    ],
    "cool": [
        "X", "7", "FX", "One",
        "Wave", "Rush", "Zero", "Xo"
    ],
    "funny": [
        "XD", "69", "Bro", "Lol",
        "King", "420", "GG", "UwU"
    ],
    "pro": [
        "YT", "GG", "FPS", "HD",
        "TV", "OP", "X", "Main"
    ],
    "cyber": [
        "404", ".exe", "X", "2077",
        "AI", "OS", "404X", "Byte"
    ],
    "fantasy": [
        "Lord", "Knight", "Mage", "Born",
        "Fang", "Fire", "Wolf", "X"
    ]
}


def clean_word(word):
    """Оставляет только английские буквы и цифры."""
    return re.sub(r"[^A-Za-z0-9]", "", word or "").strip()


def make_nickname(style, base_word=""):
    prefix = random.choice(
        PREFIXES.get(style, PREFIXES["cool"])
    )

    suffix = random.choice(
        SUFFIXES.get(style, SUFFIXES["cool"])
    )

    word = clean_word(base_word)

    patterns = [
        f"{prefix}{suffix}",
        f"{prefix}_{suffix}",
        f"{prefix}{random.randint(10, 999)}",
        f"{prefix}{word}" if word else f"{prefix}{suffix}",
        f"{word}{prefix}" if word else f"{prefix}{suffix}",
        f"{prefix}x{word}" if word else f"{prefix}x{suffix}",
    ]

    nickname = random.choice(patterns)

    return nickname[:20]


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/generate")
def generate():
    data = request.get_json(silent=True) or {}

    style = data.get("style", "cool")
    base_word = data.get("word", "")

    try:
        count = int(data.get("count", 12))
    except (TypeError, ValueError):
        count = 12

    count = min(max(count, 1), 50)

    names = []

    while len(names) < count:
        nickname = make_nickname(style, base_word)

        if nickname not in names:
            names.append(nickname)

    return jsonify({
        "names": names
    })


if __name__ == "__main__":
    app.run(debug=True)