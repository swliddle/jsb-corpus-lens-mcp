#!/usr/bin/env python3
"""Extract 4 Nephi (non-standard chapter format in Gutenberg)."""
import re
import os

GUTENBERG = "/Users/ericdenna/.gemini/antigravity/brain/5c8f70ce-7a1f-4a3d-b193-b3f80041c992/.system_generated/steps/75/content.md"
OUTPUT_DIR = "/Users/ericdenna/Library/CloudStorage/GoogleDrive-eric.denna@gmail.com/My Drive/! AAA Personal - WIP/! Joseph the Prophet/JSB - WIP/JSB Doctrinal Learning  over time/JS Revelations by Date"

with open(GUTENBERG, 'r') as f:
    text = f.read().replace('\r', '')

# Extract from "4 Nephi 1:1" to "THE BOOK OF MORMON" (the next book)
match = re.search(r'(4 Nephi 1:1.*?)(?=\n\s*THE BOOK OF MORMON\b)', text, re.DOTALL)
if not match:
    print("ERROR: Could not find 4 Nephi content")
    exit(1)

content = match.group(1).strip()
verses = len(re.findall(r'4 Nephi 1:\d+', content))
print(f"Extracted 4 Nephi: {len(content):,} chars, {verses} verses")

sep = "\u2550" * 60

# Write 1830 file
header = f"""{sep}
TEXTUAL CHANGES \u2014 4 Nephi 1, Book of Mormon, 1830 (1830-03-26)
{sep}

\u25b6 Changes from Original (1829-05-21) \u2192 Book of Mormon, 1830 (1830-03-26):

  No meaning-altering changes detected.

  NOTE: Both the Original and 1830 files currently use the Project
  Gutenberg 1830 text as their base. Differences will surface once
  the Original files are updated with Printer's Manuscript text
  and Skousen's OM corrections from the ATV.

{sep}
[Full 1830 edition text follows below]
{sep}

"""

filepath_1830 = os.path.join(OUTPUT_DIR, "1830-03-26-4Nephi-1-1830.txt")
with open(filepath_1830, 'w') as f:
    f.write(header)
    f.write("[1830-03-26]\n\n")
    f.write("FOURTH NEPHI THE BOOK OF NEPHI\n\n")
    f.write("4 Nephi Chapter 1\n\n")
    f.write(content + "\n")
print(f"  \u2713 1830-03-26-4Nephi-1-1830.txt")

filepath_orig = os.path.join(OUTPUT_DIR, "1829-05-21-4Nephi-1-Original.txt")
with open(filepath_orig, 'w') as f:
    f.write("[1829-05-21]\n\n")
    f.write("FOURTH NEPHI THE BOOK OF NEPHI\n\n")
    f.write("4 Nephi Chapter 1\n\n")
    f.write(content + "\n")
print(f"  \u2713 1829-05-21-4Nephi-1-Original.txt")

print("\nDone! 4 Nephi extracted successfully.")
