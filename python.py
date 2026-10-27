import json
from collections import Counter
from pathlib import Path

INPUT_FILE = Path("merged.json")
OUTPUT_FILE = Path("ending_stats.json")

with INPUT_FILE.open("r", encoding="utf-8") as f:
    dictionary = json.load(f)

# Count the last letter of each dictionary word
counts = Counter(
    word[-1].lower()
    for word in dictionary.keys()
    if word and word[-1].isalpha()
)

# Include letters with zero occurrences
letters = "abcdefghijklmnopqrstuvwxyz"

# Sort ascending by count, then alphabetically
sorted_letters = sorted(
    letters,
    key=lambda letter: (counts[letter], letter)
)

# Rank 1 = lowest ending count
results = {
    letter: {
        "count": counts[letter],
        "rank": rank
    }
    for rank, letter in enumerate(sorted_letters, start=1)
}

with OUTPUT_FILE.open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(f"Total dictionary words: {len(dictionary):,}")
print(f"{'Letter':<10}{'Count':<12}{'Rank'}")
print("-" * 28)

for letter, data in results.items():
    print(f"{letter:<10}{data['count']:<12}{data['rank']}")

print(f"\nSaved to {OUTPUT_FILE}")
