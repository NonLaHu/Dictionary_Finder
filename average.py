
import json
import string
from collections import defaultdict
from pathlib import Path

INPUT_FILE = Path("merged.json")
OUTPUT_FILE = Path("letter_analysis.json")

with INPUT_FILE.open("r", encoding="utf-8") as f:
    dictionary = json.load(f)

stats = defaultdict(lambda: {
    "word_count": 0,
    "total_meanings": 0,
    "total_synonyms": 0,
    "total_antonyms": 0,
    "words_with_meanings": 0,
})

for word, data in dictionary.items():
    word = word.strip().lower()

    if not word or word[0] not in string.ascii_lowercase:
        continue

    item = stats[word[0]]
    meanings = data.get("MEANINGS", [])
    synonyms = data.get("SYNONYMS", [])
    antonyms = data.get("ANTONYMS", [])

    item["word_count"] += 1
    item["total_meanings"] += len(meanings)
    item["total_synonyms"] += len(synonyms)
    item["total_antonyms"] += len(antonyms)

    if meanings:
        item["words_with_meanings"] += 1

results = {}

for letter in string.ascii_lowercase:
    item = stats[letter]
    count = item["word_count"]

    results[letter] = {
        "word_count": count,
        "total_meanings": item["total_meanings"],
        "average_meanings_per_word": round(
            item["total_meanings"] / count, 3
        ) if count else 0,
        "average_synonyms_per_word": round(
            item["total_synonyms"] / count, 3
        ) if count else 0,
        "average_antonyms_per_word": round(
            item["total_antonyms"] / count, 3
        ) if count else 0,
        "words_with_meanings_percent": round(
            item["words_with_meanings"] / count * 100, 2
        ) if count else 0,
    }

# Rank each metric independently: rank 1 = highest value
metrics = [
    "word_count",
    "total_meanings",
    "average_meanings_per_word",
    "average_synonyms_per_word",
]

for metric in metrics:
    ordered = sorted(
        results,
        key=lambda letter: (-results[letter][metric], letter)
    )

    rank = 0
    previous_value = None

    for position, letter in enumerate(ordered, start=1):
        value = results[letter][metric]

        if value != previous_value:
            rank = position

        results[letter][metric + "_rank"] = rank
        previous_value = value

with OUTPUT_FILE.open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"{'Letter':<8}{'Words':>10}{'Meanings':>12}"
      f"{'Avg meanings':>15}{'Avg synonyms':>15}")

for letter in sorted(
    results,
    key=lambda x: results[x]["word_count"],
    reverse=True
):
    d = results[letter]
    print(
        f"{letter:<8}{d['word_count']:>10}"
        f"{d['total_meanings']:>12}"
        f"{d['average_meanings_per_word']:>15.2f}"
        f"{d['average_synonyms_per_word']:>15.2f}"
    )

print(f"\nSaved to {OUTPUT_FILE}")
