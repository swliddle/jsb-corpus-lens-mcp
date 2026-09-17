#!/usr/bin/env python3
"""
Extract single-chapter books that don't use "Chapter 1" format in Gutenberg.
Books: Enos, Jarom, Omni, Words of Mormon
"""
import re
import os

GUTENBERG = "/Users/ericdenna/.gemini/antigravity/brain/5c8f70ce-7a1f-4a3d-b193-b3f80041c992/.system_generated/steps/75/content.md"
OUTPUT_DIR = "/Users/ericdenna/Library/CloudStorage/GoogleDrive-eric.denna@gmail.com/My Drive/! AAA Personal - WIP/! Joseph the Prophet/JSB - WIP/JSB Doctrinal Learning  over time/JS Revelations by Date"

with open(GUTENBERG, 'r') as f:
    text = f.read().replace('\r', '')

# Define single-chapter books with their extraction patterns
books = [
    {
        "name": "Enos",
        "prefix": "Enos",
        "date": "1829-06-27",
        "start": r'THE BOOK OF ENOS\s*\n',
        "end": r'\n\s*THE BOOK OF JAROM',
        "preamble": "THE BOOK OF ENOS",
        "verse_pattern": r'1:\d+',
    },
    {
        "name": "Jarom",
        "prefix": "Jarom",
        "date": "1829-06-27",
        "start": r'THE BOOK OF JAROM\s*\n',
        "end": r'\n\s*THE BOOK OF OMNI',
        "preamble": "THE BOOK OF JAROM",
        "verse_pattern": r'1:\d+',
    },
    {
        "name": "Omni",
        "prefix": "Omni",
        "date": "1829-06-28",
        "start": r'THE BOOK OF OMNI\s*\n',
        "end": r'\n\s*THE WORDS OF MORMON',
        "preamble": "THE BOOK OF OMNI",
        "verse_pattern": r'1:\d+',
    },
    {
        "name": "Words of Mormon",
        "prefix": "WordsOfMormon",
        "date": "1829-06-28",
        "start": r'THE WORDS OF MORMON\s*\n',
        "end": r'\n\s*THE BOOK OF MOSIAH',
        "preamble": "THE WORDS OF MORMON",
        "verse_pattern": r'1:\d+',
    },
]

sep = "\u2550" * 60

for book in books:
    # Find the second occurrence (first is table of contents)
    all_matches = list(re.finditer(book["start"], text))
    if len(all_matches) < 2:
        print(f"ERROR: Could not find second occurrence of {book['name']} header")
        continue

    start_pos = all_matches[1].end()

    # Find the end marker
    end_match = re.search(book["end"], text[start_pos:])
    if not end_match:
        print(f"ERROR: Could not find end marker for {book['name']}")
        continue

    content = text[start_pos:start_pos + end_match.start()].strip()
    verses = len(re.findall(book["verse_pattern"], content))
    print(f"{book['name']}: {len(content):,} chars, {verses} verses")

    # Build diff header
    header = f"""{sep}
TEXTUAL CHANGES \u2014 {book['name']} 1, Book of Mormon, 1830 (1830-03-26)
{sep}

\u25b6 Changes from Original ({book['date']}) \u2192 Book of Mormon, 1830 (1830-03-26):

  No meaning-altering changes detected.

  NOTE: Both the Original and 1830 files currently use the Project
  Gutenberg 1830 text as their base. Differences will surface once
  the Original files are updated with Printer's Manuscript text
  and Skousen's OM corrections from the ATV.

{sep}
[Full 1830 edition text follows below]
{sep}

"""

    # Write 1830 file
    filepath_1830 = os.path.join(OUTPUT_DIR, f"1830-03-26-{book['prefix']}-1-1830.txt")
    with open(filepath_1830, 'w') as f:
        f.write(header)
        f.write(f"[1830-03-26]\n\n")
        f.write(f"{book['preamble']}\n\n")
        f.write(content + "\n")
    print(f"  \u2713 1830-03-26-{book['prefix']}-1-1830.txt")

    # Write Original file
    filepath_orig = os.path.join(OUTPUT_DIR, f"{book['date']}-{book['prefix']}-1-Original.txt")
    with open(filepath_orig, 'w') as f:
        f.write(f"[{book['date']}]\n\n")
        f.write(f"{book['preamble']}\n\n")
        f.write(content + "\n")
    print(f"  \u2713 {book['date']}-{book['prefix']}-1-Original.txt")

print("\nDone! All single-chapter books extracted.")
