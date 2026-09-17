#!/usr/bin/env python3
"""
Book of Mormon 1 Nephi Pilot Extraction Script
===============================================
Parses the Project Gutenberg 1830 text and creates per-chapter files for:
  1. 1830 Edition:  1830-03-26-1Nephi-{ch}-1830.txt
  2. Original Translation: {date}-1Nephi-{ch}-Original.txt

The "Original" files use the same Gutenberg text as a starting point
(since the 1830 edition IS the first print of the original translation).
OM corrections from Skousen's ATV will be applied in a subsequent pass.
"""

import os
import re

# === CONFIGURATION ===

GUTENBERG_FILE = "/Users/ericdenna/.gemini/antigravity/brain/5c8f70ce-7a1f-4a3d-b193-b3f80041c992/.system_generated/steps/75/content.md"

OUTPUT_DIR = "/Users/ericdenna/Library/CloudStorage/GoogleDrive-eric.denna@gmail.com/My Drive/! AAA Personal - WIP/! Joseph the Prophet/JSB - WIP/JSB Doctrinal Learning  over time/JS Revelations by Date"

# Chapter-to-translation-date mapping (from Welch 2018 / existing BOM files)
CHAPTER_DATES = {
    1: "1829-06-05",
    2: "1829-06-05",
    3: "1829-06-06",
    4: "1829-06-06",
    5: "1829-06-06",
    6: "1829-06-06",
    7: "1829-06-07",
    8: "1829-06-07",
    9: "1829-06-07",
    10: "1829-06-08",
    11: "1829-06-08",
    12: "1829-06-08",
    13: "1829-06-09",
    14: "1829-06-09",
    15: "1829-06-09",
    16: "1829-06-10",
    17: "1829-06-10",
    18: "1829-06-10",
    19: "1829-06-10",
    20: "1829-06-12",
    21: "1829-06-12",
    22: "1829-06-12",
}


def read_gutenberg_text(filepath):
    """Read the Gutenberg plain text file, stripping the markdown header."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Strip the markdown source header (lines before the actual Gutenberg content)
    if '---' in content:
        parts = content.split('---', 1)
        if len(parts) > 1:
            content = parts[1]

    return content


def extract_1nephi_chapters(text):
    """Extract 1 Nephi chapters 1-22 from the Gutenberg text."""
    chapters = {}

    # Also grab the book preamble (header/summary before chapter 1)
    preamble_match = re.search(
        r'THE FIRST BOOK OF NEPHI HIS REIGN AND MINISTRY \(1 Nephi\)\s*\n\s*\n(.*?)(?=1 Nephi Chapter 1)',
        text, re.DOTALL
    )
    preamble = preamble_match.group(1).strip() if preamble_match else ""

    for ch in range(1, 23):
        # Find the chapter start
        pattern_start = rf'1 Nephi Chapter {ch}\s*\n'

        if ch < 22:
            # Find text between this chapter header and the next
            pattern_end = rf'1 Nephi Chapter {ch + 1}\s*\n'
            match = re.search(pattern_start + r'(.*?)' + pattern_end, text, re.DOTALL)
        else:
            # Last chapter (22) — find text until the next book
            # 2 Nephi starts after 1 Nephi 22
            pattern_end = r'(?:THE SECOND BOOK OF NEPHI|2 Nephi Chapter 1)'
            match = re.search(pattern_start + r'(.*?)' + pattern_end, text, re.DOTALL)

        if match:
            chapter_text = match.group(1).strip()
            # Clean up: remove \r characters
            chapter_text = chapter_text.replace('\r', '')
            chapters[ch] = chapter_text
        else:
            print(f"WARNING: Could not extract 1 Nephi Chapter {ch}")

    return chapters, preamble


def write_chapter_file(filepath, date_str, book, chapter, edition, text, preamble=None):
    """Write a single chapter file in the established format."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"[{date_str}]\n\n")

        # Include preamble for chapter 1
        if preamble and chapter == 1:
            f.write(f"{book}\n\n")
            f.write(f"{preamble}\n\n\n")

        f.write(f"1 Nephi Chapter {chapter}\n\n\n")
        f.write(text)
        f.write("\n")


def main():
    print("=" * 60)
    print("Book of Mormon 1 Nephi Extraction — Pilot Batch")
    print("=" * 60)

    # Step 1: Read Gutenberg text
    print("\n[1] Reading Gutenberg 1830 text...")
    text = read_gutenberg_text(GUTENBERG_FILE)
    print(f"    Read {len(text):,} characters")

    # Step 2: Extract 1 Nephi chapters
    print("\n[2] Extracting 1 Nephi chapters 1-22...")
    chapters, preamble = extract_1nephi_chapters(text)
    print(f"    Extracted {len(chapters)} chapters")
    for ch, txt in sorted(chapters.items()):
        verse_count = len(re.findall(r'\d+:\d+', txt))
        print(f"    Chapter {ch:2d}: {len(txt):5,} chars, ~{verse_count} verses")

    # Step 3: Write 1830 Edition files
    print("\n[3] Writing 1830 Edition files...")
    edition_1830_count = 0
    for ch, txt in sorted(chapters.items()):
        filename = f"1830-03-26-1Nephi-{ch}-1830.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        write_chapter_file(filepath, "1830-03-26", "THE FIRST BOOK OF NEPHI HIS REIGN AND MINISTRY (1 Nephi)", ch, "1830", txt, preamble if ch == 1 else None)
        edition_1830_count += 1
        print(f"    ✓ {filename}")

    # Step 4: Write Original Translation files
    print("\n[4] Writing Original Translation files...")
    original_count = 0
    for ch, txt in sorted(chapters.items()):
        date = CHAPTER_DATES[ch]
        filename = f"{date}-1Nephi-{ch}-Original.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        write_chapter_file(filepath, date, "THE FIRST BOOK OF NEPHI HIS REIGN AND MINISTRY (1 Nephi)", ch, "Original", txt, preamble if ch == 1 else None)
        original_count += 1
        print(f"    ✓ {filename}")

    # Summary
    print("\n" + "=" * 60)
    print(f"COMPLETE: Created {edition_1830_count + original_count} files")
    print(f"  - 1830 Edition:  {edition_1830_count} files")
    print(f"  - Original:      {original_count} files")
    print(f"  - Output dir:    {OUTPUT_DIR}")
    print("=" * 60)
    print("\nNOTE: The 'Original' files currently use the 1830 text as a")
    print("starting point. OM corrections from Skousen's ATV will be")
    print("applied in a subsequent pass.")


if __name__ == "__main__":
    main()
