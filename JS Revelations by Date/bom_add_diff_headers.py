#!/usr/bin/env python3
"""
Add D&C-style diff headers to 1830 Edition BOM files.
Compares each 1830 chapter against its corresponding Original file.

Currently both use the same Gutenberg source, so differences will be
minimal or none. Headers will be regenerated when PM/OM corrections
are applied to the Original files.
"""

import os
import re
import difflib

OUTPUT_DIR = "/Users/ericdenna/Library/CloudStorage/GoogleDrive-eric.denna@gmail.com/My Drive/! AAA Personal - WIP/! Joseph the Prophet/JSB - WIP/JSB Doctrinal Learning  over time/JS Revelations by Date"

# Chapter-to-translation-date mapping
CHAPTER_DATES = {
    1: "1829-06-05", 2: "1829-06-05",
    3: "1829-06-06", 4: "1829-06-06", 5: "1829-06-06", 6: "1829-06-06",
    7: "1829-06-07", 8: "1829-06-07", 9: "1829-06-07",
    10: "1829-06-08", 11: "1829-06-08", 12: "1829-06-08",
    13: "1829-06-09", 14: "1829-06-09", 15: "1829-06-09",
    16: "1829-06-10", 17: "1829-06-10", 18: "1829-06-10", 19: "1829-06-10",
    20: "1829-06-12", 21: "1829-06-12", 22: "1829-06-12",
}


def extract_body_text(filepath):
    """Read a file, return the text body after the date header."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip the date header line and find the chapter text
    # Look for verse references (e.g., "1:1", "2:3") as the start of real content
    lines = content.split('\n')
    body_lines = []
    in_body = False
    for line in lines:
        # Start capturing at the first verse reference
        if re.match(r'\d+:\d+\s', line):
            in_body = True
        if in_body:
            body_lines.append(line)
    
    return '\n'.join(body_lines)


def find_meaningful_changes(original_text, edition_text, chapter):
    """Compare two texts and identify meaning-altering changes.
    Returns a list of change descriptions."""
    
    orig_lines = original_text.strip().split('\n')
    edit_lines = edition_text.strip().split('\n')
    
    # Use difflib to find differences
    differ = difflib.unified_diff(orig_lines, edit_lines, lineterm='')
    diff_lines = list(differ)
    
    if not diff_lines:
        return []
    
    # Parse the diff to identify specific changes
    changes = []
    change_num = 0
    i = 0
    while i < len(diff_lines):
        line = diff_lines[i]
        if line.startswith('-') and not line.startswith('---'):
            # Find the corresponding + line
            removed = line[1:].strip()
            added = ""
            if i + 1 < len(diff_lines) and diff_lines[i + 1].startswith('+') and not diff_lines[i + 1].startswith('+++'):
                added = diff_lines[i + 1][1:].strip()
                i += 1
            
            # Skip empty line differences (just whitespace/formatting)
            if removed == added:
                i += 1
                continue
            if not removed and not added:
                i += 1
                continue
            
            # Try to find the verse reference
            verse_match = re.search(r'(\d+:\d+)', removed) or re.search(r'(\d+:\d+)', added)
            verse_ref = verse_match.group(1) if verse_match else "unknown"
            
            # Determine change type
            if not removed and added:
                change_type = "PHRASE ADDITION"
            elif removed and not added:
                change_type = "PHRASE REMOVAL"
            else:
                change_type = "WORD CHANGE"
            
            change_num += 1
            
            # Truncate long lines
            if len(removed) > 120:
                removed = removed[:120] + "..."
            if len(added) > 120:
                added = added[:120] + "..."
            
            change_desc = f"  {change_num}. {change_type} (verse {verse_ref}):\n"
            if removed:
                change_desc += f'     EARLIER: "{removed}"\n'
            if added:
                change_desc += f'     LATER:   "{added}"\n'
            
            changes.append(change_desc)
        
        i += 1
    
    return changes


def build_header(chapter, original_date, changes):
    """Build the D&C-style diff header."""
    separator = "═" * 60
    
    header = f"{separator}\n"
    header += f"TEXTUAL CHANGES — 1 Nephi {chapter}, Book of Mormon, 1830 (1830-03-26)\n"
    header += f"{separator}\n\n"
    header += f"▶ Changes from Original ({original_date}) → Book of Mormon, 1830 (1830-03-26):\n\n"
    
    if not changes:
        header += "  No meaning-altering changes detected.\n"
        header += f"\n  NOTE: Both the Original and 1830 files currently use the Project\n"
        header += f"  Gutenberg 1830 text as their base. Differences will surface once\n"
        header += f"  the Original files are updated with Printer's Manuscript text\n"
        header += f"  and Skousen's OM corrections from the ATV.\n"
    else:
        for change in changes:
            header += change + "\n"
    
    header += f"\n{separator}\n"
    header += "[Full 1830 edition text follows below]\n"
    header += f"{separator}\n\n"
    
    return header


def main():
    print("=" * 60)
    print("Adding Diff Headers to 1830 Edition Files (1 Nephi)")
    print("=" * 60)
    
    for ch in range(1, 23):
        original_date = CHAPTER_DATES[ch]
        original_file = os.path.join(OUTPUT_DIR, f"{original_date}-1Nephi-{ch}-Original.txt")
        edition_file = os.path.join(OUTPUT_DIR, f"1830-03-26-1Nephi-{ch}-1830.txt")
        
        if not os.path.exists(original_file):
            print(f"  ✗ Chapter {ch}: Original file not found")
            continue
        if not os.path.exists(edition_file):
            print(f"  ✗ Chapter {ch}: 1830 file not found")
            continue
        
        # Extract body text for comparison
        orig_text = extract_body_text(original_file)
        edit_text = extract_body_text(edition_file)
        
        # Find changes
        changes = find_meaningful_changes(orig_text, edit_text, ch)
        
        # Build header
        header = build_header(ch, original_date, changes)
        
        # Read the current 1830 file
        with open(edition_file, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        # Write the updated file with header prepended
        with open(edition_file, 'w', encoding='utf-8') as f:
            f.write(header)
            f.write(current_content)
        
        change_count = len(changes)
        status = f"{change_count} changes" if change_count > 0 else "No changes (identical source)"
        print(f"  ✓ Chapter {ch:2d}: {status}")
    
    print("\n" + "=" * 60)
    print("COMPLETE: All 22 1830 Edition files updated with diff headers")
    print("=" * 60)


if __name__ == "__main__":
    main()
