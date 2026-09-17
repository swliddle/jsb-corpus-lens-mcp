#!/usr/bin/env python3
"""
Update all existing 1830 and Original files with BomDB data.
=============================================================
Replaces:
  - Original files: Gutenberg text → BomDB 1829 Printer's Manuscript text
  - 1830 files: 
    * Gutenberg text → BomDB 1830 Palmyra text
    * Placeholder headers → Real diff headers (1829 PM vs 1830)
"""

import json
import os
import re

BOMDB_FILE = "/Users/ericdenna/Library/CloudStorage/GoogleDrive-eric.denna@gmail.com/My Drive/! AAA Personal - WIP/! Joseph the Prophet/JSB - WIP/JSB Doctrinal Learning  over time/JS Revelations by Date/bomdb_contents.json"

OUTPUT_DIR = "/Users/ericdenna/Library/CloudStorage/GoogleDrive-eric.denna@gmail.com/My Drive/! AAA Personal - WIP/! Joseph the Prophet/JSB - WIP/JSB Doctrinal Learning  over time/JS Revelations by Date"

# Book name mapping: BomDB name → our file prefix
BOOK_MAP = {
    "1 Nephi": "1Nephi", "2 Nephi": "2Nephi", "Jacob": "Jacob",
    "Enos": "Enos", "Jarom": "Jarom", "Omni": "Omni",
    "Words of Mormon": "WordsOfMormon", "Mosiah": "Mosiah",
    "Alma": "Alma", "Helaman": "Helaman", "3 Nephi": "3Nephi",
    "4 Nephi": "4Nephi", "Mormon": "Mormon", "Ether": "Ether",
    "Moroni": "Moroni",
}

# Translation dates (same as from previous scripts)
CHAPTER_DATES = {
    ("Mosiah", 1): "1829-03-31",
    ("Mosiah", 2): "1829-04-07", ("Mosiah", 3): "1829-04-07", ("Mosiah", 4): "1829-04-07",
    ("Mosiah", 5): "1829-04-08", ("Mosiah", 6): "1829-04-08", ("Mosiah", 7): "1829-04-08",
    ("Mosiah", 8): "1829-04-09", ("Mosiah", 9): "1829-04-09", ("Mosiah", 10): "1829-04-09", ("Mosiah", 11): "1829-04-09",
    ("Mosiah", 12): "1829-04-10", ("Mosiah", 13): "1829-04-10", ("Mosiah", 14): "1829-04-10", ("Mosiah", 15): "1829-04-10", ("Mosiah", 16): "1829-04-10",
    ("Mosiah", 17): "1829-04-11", ("Mosiah", 18): "1829-04-11", ("Mosiah", 19): "1829-04-11", ("Mosiah", 20): "1829-04-11",
    ("Mosiah", 21): "1829-04-12", ("Mosiah", 22): "1829-04-12", ("Mosiah", 23): "1829-04-12", ("Mosiah", 24): "1829-04-12", ("Mosiah", 25): "1829-04-12",
    ("Mosiah", 26): "1829-04-13", ("Mosiah", 27): "1829-04-13", ("Mosiah", 28): "1829-04-13",
    ("Mosiah", 29): "1829-04-14",
    ("Alma", 1): "1829-04-14", ("Alma", 2): "1829-04-14",
    ("Alma", 3): "1829-04-15", ("Alma", 4): "1829-04-15", ("Alma", 5): "1829-04-15", ("Alma", 6): "1829-04-15",
    ("Alma", 7): "1829-04-16", ("Alma", 8): "1829-04-16", ("Alma", 9): "1829-04-16", ("Alma", 10): "1829-04-16",
    ("Alma", 11): "1829-04-17", ("Alma", 12): "1829-04-17", ("Alma", 13): "1829-04-17",
    ("Alma", 14): "1829-04-18", ("Alma", 15): "1829-04-18", ("Alma", 16): "1829-04-18", ("Alma", 17): "1829-04-18",
    ("Alma", 18): "1829-04-19", ("Alma", 19): "1829-04-19",
    ("Alma", 20): "1829-04-20", ("Alma", 21): "1829-04-20", ("Alma", 22): "1829-04-20", ("Alma", 23): "1829-04-20",
    ("Alma", 24): "1829-04-21", ("Alma", 25): "1829-04-21", ("Alma", 26): "1829-04-21",
    ("Alma", 27): "1829-04-22", ("Alma", 28): "1829-04-22", ("Alma", 29): "1829-04-22", ("Alma", 30): "1829-04-22",
    ("Alma", 31): "1829-04-23", ("Alma", 32): "1829-04-23", ("Alma", 33): "1829-04-23",
    ("Alma", 34): "1829-04-24", ("Alma", 35): "1829-04-24", ("Alma", 36): "1829-04-24",
    ("Alma", 37): "1829-04-25", ("Alma", 38): "1829-04-25",
    ("Alma", 39): "1829-04-26", ("Alma", 40): "1829-04-26",
    ("Alma", 41): "1829-04-27", ("Alma", 42): "1829-04-27", ("Alma", 43): "1829-04-27",
    ("Alma", 44): "1829-04-28", ("Alma", 45): "1829-04-28",
    ("Alma", 46): "1829-04-29", ("Alma", 47): "1829-04-29", ("Alma", 48): "1829-04-29",
    ("Alma", 49): "1829-04-30", ("Alma", 50): "1829-04-30", ("Alma", 51): "1829-04-30",
    ("Alma", 52): "1829-05-01", ("Alma", 53): "1829-05-01", ("Alma", 54): "1829-05-01",
    ("Alma", 55): "1829-05-02", ("Alma", 56): "1829-05-02", ("Alma", 57): "1829-05-02",
    ("Alma", 58): "1829-05-03", ("Alma", 59): "1829-05-03", ("Alma", 60): "1829-05-03", ("Alma", 61): "1829-05-03",
    ("Alma", 62): "1829-05-04", ("Alma", 63): "1829-05-04",
    ("Helaman", 1): "1829-05-04",
    ("Helaman", 2): "1829-05-05", ("Helaman", 3): "1829-05-05", ("Helaman", 4): "1829-05-05",
    ("Helaman", 5): "1829-05-06", ("Helaman", 6): "1829-05-06", ("Helaman", 7): "1829-05-06",
    ("Helaman", 8): "1829-05-07", ("Helaman", 9): "1829-05-07", ("Helaman", 10): "1829-05-07",
    ("Helaman", 11): "1829-05-08", ("Helaman", 12): "1829-05-08", ("Helaman", 13): "1829-05-08",
    ("Helaman", 14): "1829-05-09", ("Helaman", 15): "1829-05-09", ("Helaman", 16): "1829-05-09",
    ("3 Nephi", 1): "1829-05-10", ("3 Nephi", 2): "1829-05-10", ("3 Nephi", 3): "1829-05-10",
    ("3 Nephi", 4): "1829-05-11", ("3 Nephi", 5): "1829-05-11", ("3 Nephi", 6): "1829-05-11",
    ("3 Nephi", 7): "1829-05-12", ("3 Nephi", 8): "1829-05-12", ("3 Nephi", 9): "1829-05-12", ("3 Nephi", 10): "1829-05-12",
    ("3 Nephi", 11): "1829-05-13", ("3 Nephi", 12): "1829-05-13",
    ("3 Nephi", 13): "1829-05-14", ("3 Nephi", 14): "1829-05-14", ("3 Nephi", 15): "1829-05-14",
    ("3 Nephi", 16): "1829-05-15", ("3 Nephi", 17): "1829-05-15", ("3 Nephi", 18): "1829-05-15",
    ("3 Nephi", 19): "1829-05-16", ("3 Nephi", 20): "1829-05-16", ("3 Nephi", 21): "1829-05-16",
    ("3 Nephi", 22): "1829-05-17", ("3 Nephi", 23): "1829-05-17",
    ("3 Nephi", 24): "1829-05-20", ("3 Nephi", 25): "1829-05-20", ("3 Nephi", 26): "1829-05-20", ("3 Nephi", 27): "1829-05-20",
    ("3 Nephi", 28): "1829-05-21", ("3 Nephi", 29): "1829-05-21", ("3 Nephi", 30): "1829-05-21",
    ("4 Nephi", 1): "1829-05-21",
    ("Mormon", 1): "1829-05-22", ("Mormon", 2): "1829-05-22", ("Mormon", 3): "1829-05-22", ("Mormon", 4): "1829-05-22",
    ("Mormon", 5): "1829-05-23", ("Mormon", 6): "1829-05-23", ("Mormon", 7): "1829-05-23",
    ("Mormon", 8): "1829-05-24", ("Mormon", 9): "1829-05-24",
    ("Ether", 1): "1829-05-25", ("Ether", 2): "1829-05-25", ("Ether", 3): "1829-05-25",
    ("Ether", 4): "1829-05-26", ("Ether", 5): "1829-05-26", ("Ether", 6): "1829-05-26", ("Ether", 7): "1829-05-26",
    ("Ether", 8): "1829-05-27", ("Ether", 9): "1829-05-27", ("Ether", 10): "1829-05-27",
    ("Ether", 11): "1829-05-28", ("Ether", 12): "1829-05-28",
    ("Ether", 13): "1829-05-29", ("Ether", 14): "1829-05-29", ("Ether", 15): "1829-05-29",
    ("Moroni", 1): "1829-05-29", ("Moroni", 2): "1829-05-29", ("Moroni", 3): "1829-05-29", ("Moroni", 4): "1829-05-29",
    ("Moroni", 5): "1829-05-30", ("Moroni", 6): "1829-05-30", ("Moroni", 7): "1829-05-30", ("Moroni", 8): "1829-05-30",
    ("Moroni", 9): "1829-05-31", ("Moroni", 10): "1829-05-31",
    ("1 Nephi", 1): "1829-06-05", ("1 Nephi", 2): "1829-06-05",
    ("1 Nephi", 3): "1829-06-06", ("1 Nephi", 4): "1829-06-06", ("1 Nephi", 5): "1829-06-06", ("1 Nephi", 6): "1829-06-06",
    ("1 Nephi", 7): "1829-06-07", ("1 Nephi", 8): "1829-06-07", ("1 Nephi", 9): "1829-06-07",
    ("1 Nephi", 10): "1829-06-08", ("1 Nephi", 11): "1829-06-08", ("1 Nephi", 12): "1829-06-08",
    ("1 Nephi", 13): "1829-06-09", ("1 Nephi", 14): "1829-06-09", ("1 Nephi", 15): "1829-06-09",
    ("1 Nephi", 16): "1829-06-10", ("1 Nephi", 17): "1829-06-10", ("1 Nephi", 18): "1829-06-10", ("1 Nephi", 19): "1829-06-10",
    ("1 Nephi", 20): "1829-06-12", ("1 Nephi", 21): "1829-06-12", ("1 Nephi", 22): "1829-06-12",
    ("2 Nephi", 1): "1829-06-13", ("2 Nephi", 2): "1829-06-13", ("2 Nephi", 3): "1829-06-13",
    ("2 Nephi", 4): "1829-06-15", ("2 Nephi", 5): "1829-06-15", ("2 Nephi", 6): "1829-06-15",
    ("2 Nephi", 7): "1829-06-16", ("2 Nephi", 8): "1829-06-16", ("2 Nephi", 9): "1829-06-16",
    ("2 Nephi", 10): "1829-06-17", ("2 Nephi", 11): "1829-06-17", ("2 Nephi", 12): "1829-06-17", ("2 Nephi", 13): "1829-06-17",
    ("2 Nephi", 14): "1829-06-18", ("2 Nephi", 15): "1829-06-18", ("2 Nephi", 16): "1829-06-18", ("2 Nephi", 17): "1829-06-18", ("2 Nephi", 18): "1829-06-18", ("2 Nephi", 19): "1829-06-18",
    ("2 Nephi", 20): "1829-06-19", ("2 Nephi", 21): "1829-06-19", ("2 Nephi", 22): "1829-06-19", ("2 Nephi", 23): "1829-06-19", ("2 Nephi", 24): "1829-06-19",
    ("2 Nephi", 25): "1829-06-20", ("2 Nephi", 26): "1829-06-20", ("2 Nephi", 27): "1829-06-20",
    ("2 Nephi", 28): "1829-06-22", ("2 Nephi", 29): "1829-06-22", ("2 Nephi", 30): "1829-06-22", ("2 Nephi", 31): "1829-06-22",
    ("2 Nephi", 32): "1829-06-23", ("2 Nephi", 33): "1829-06-23",
    ("Jacob", 1): "1829-06-24", ("Jacob", 2): "1829-06-24", ("Jacob", 3): "1829-06-24",
    ("Jacob", 4): "1829-06-25", ("Jacob", 5): "1829-06-25",
    ("Jacob", 6): "1829-06-26", ("Jacob", 7): "1829-06-26",
    ("Enos", 1): "1829-06-27", ("Jarom", 1): "1829-06-27",
    ("Omni", 1): "1829-06-28", ("Words of Mormon", 1): "1829-06-28",
}


def find_meaning_changes(earlier_verses, later_verses, verse_refs):
    """Compare two sets of verse texts and identify meaning-altering changes."""
    changes = []
    change_num = 0
    
    for ref in verse_refs:
        earlier = earlier_verses.get(ref, "")
        later = later_verses.get(ref, "")
        
        if earlier == later:
            continue
        
        e_norm = re.sub(r'[;:,.\-\!\?]', '', earlier.lower()).split()
        l_norm = re.sub(r'[;:,.\-\!\?]', '', later.lower()).split()
        
        if e_norm == l_norm:
            continue
        
        e_set = set(e_norm)
        l_set = set(l_norm)
        added_words = l_set - e_set
        removed_words = e_set - l_set
        
        if not added_words and not removed_words:
            continue
        
        change_num += 1
        
        if len(earlier) < len(later) * 0.7:
            change_type = "PHRASE ADDITION"
        elif len(later) < len(earlier) * 0.7:
            change_type = "PHRASE REMOVAL"
        else:
            change_type = "WORD CHANGE"
        
        e_display = earlier[:150] + "..." if len(earlier) > 150 else earlier
        l_display = later[:150] + "..." if len(later) > 150 else later
        
        changes.append(
            f"  {change_num}. {change_type} ({ref}):\n"
            f'     EARLIER: "{e_display}"\n'
            f'     LATER:   "{l_display}"\n'
        )
    
    return changes


def main():
    print("=" * 70)
    print("Upgrading Original & 1830 Files with BomDB Data")
    print("=" * 70)
    
    with open(BOMDB_FILE, 'r') as f:
        data = json.load(f)
    
    contents = data["contents"]
    sep = "\u2550" * 60
    
    orig_updated = 0
    e1830_updated = 0
    total_changes = 0
    
    for book_name, chapters in contents.items():
        prefix = BOOK_MAP.get(book_name)
        if not prefix:
            continue
        
        for ch_str, verses in sorted(chapters.items(), key=lambda x: int(x[0])):
            ch = int(ch_str)
            date_key = (book_name, ch)
            orig_date = CHAPTER_DATES.get(date_key, "unknown")
            
            # Sort verse refs
            verse_refs = sorted(verses.keys(), key=lambda v: [int(x) for x in re.findall(r'\d+', v)])
            
            # --- UPDATE ORIGINAL FILE ---
            orig_filename = f"{orig_date}-{prefix}-{ch}-Original.txt"
            orig_filepath = os.path.join(OUTPUT_DIR, orig_filename)
            
            orig_text_parts = []
            for ref in verse_refs:
                text = verses[ref].get("1829", "")
                if text:
                    orig_text_parts.append(f"{ref} {text}")
            
            orig_text = "\n\n".join(orig_text_parts)
            
            with open(orig_filepath, 'w') as f:
                f.write(f"[{orig_date}]\n\n")
                f.write(orig_text)
                f.write("\n")
            orig_updated += 1
            
            # --- UPDATE 1830 FILE (with real diff headers) ---
            e1830_filename = f"1830-03-26-{prefix}-{ch}-1830.txt"
            e1830_filepath = os.path.join(OUTPUT_DIR, e1830_filename)
            
            # Build verse maps
            pm_verses = {}
            e1830_verses = {}
            for ref in verse_refs:
                pm_verses[ref] = verses[ref].get("1829", "")
                e1830_verses[ref] = verses[ref].get("1830", "")
            
            changes = find_meaning_changes(pm_verses, e1830_verses, verse_refs)
            total_changes += len(changes)
            
            # Build header
            header = f"{sep}\n"
            header += f"TEXTUAL CHANGES \u2014 {book_name} {ch}, Book of Mormon, 1830 Palmyra (1830-03-26)\n"
            header += f"{sep}\n\n"
            header += f"\u25b6 Changes from 1829 Printer's Manuscript ({orig_date}) \u2192 1830 Palmyra (1830-03-26):\n\n"
            
            if not changes:
                header += "  No meaning-altering changes detected.\n"
            else:
                for change in changes:
                    header += change + "\n"
            
            header += f"\n{sep}\n"
            header += f"[Full 1830 Palmyra edition text follows below]\n"
            header += f"{sep}\n\n"
            
            # Build 1830 text
            e1830_text_parts = []
            for ref in verse_refs:
                text = e1830_verses.get(ref, "")
                if text:
                    e1830_text_parts.append(f"{ref} {text}")
            
            e1830_text = "\n\n".join(e1830_text_parts)
            
            with open(e1830_filepath, 'w') as f:
                f.write(header)
                f.write(f"[1830-03-26]\n\n")
                f.write(e1830_text)
                f.write("\n")
            e1830_updated += 1
    
    print(f"\n  Original files updated: {orig_updated}")
    print(f"  1830 files updated:     {e1830_updated}")
    print(f"  PM→1830 changes found:  {total_changes}")
    print("\nDone!")


if __name__ == "__main__":
    main()
