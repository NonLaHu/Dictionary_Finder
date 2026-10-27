
import json
from collections import Counter
from pathlib import Path

INPUT_FILE = Path("merged.json")
OUTPUT_FILE = Path("starting_stats.json")

with INPUT_FILE.open("r", encoding="utf-8") as f:
    dictionary = json.load(f)

letters = "abcdefghijklmnopqrstuvwxyz"

# Count words by their FIRST letter
counts = Counter(
    word[0].lower()
    for word in dictionary
    if word and word[0].lower() in letters
)

# Sort by lowest count, then alphabetically
sorted_letters = sorted(
    letters,
    key=lambda letter: (counts[letter], letter)
)

# Equal counts receive equal ranks
unique_counts = sorted(set(counts[letter] for letter in letters))
rank_map = {
    count: rank
    for rank, count in enumerate(unique_counts, start=1)
}

results = {
    letter: {
        "count": counts[letter],
        "rank": rank_map[counts[letter]]
    }
    for letter in sorted_letters
}

with OUTPUT_FILE.open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print(f"Total words: {len(dictionary):,}")
print(f"{'Letter':<10}{'Count':<12}{'Rank'}")
print("-" * 28)

for letter, data in results.items():
    print(f"{letter:<10}{data['count']:<12}{data['rank']}")

print(f"\nSaved to {OUTPUT_FILE}")
