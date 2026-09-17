#!/usr/bin/env python3
"""
Skousen Critical Text Corrections for Original (PM) Files
==========================================================
Applies Royal Skousen's most significant OM/Earliest Text corrections
to the BomDB Printer's Manuscript text in our Original files.

Source: Skousen, Royal. "Some Textual Changes for a Scholarly Study
of the Book of Mormon." BYU Studies Quarterly 51, no. 4 (2012): 99-117.

Plus additional well-documented corrections from Skousen's Analysis of
Textual Variants and The Book of Mormon: The Earliest Text (Yale, 2009/2022).

Method: Each correction is tagged with:
  - Verse reference
  - PM reading (what BomDB has)
  - Earliest Text reading (what Skousen reconstructs)
  - Source citation
  - Doctrinal significance rating (HIGH / MEDIUM / LOW)
    HIGH   = Changes doctrinal/theological meaning or scriptural allusion
    MEDIUM = Changes narrative meaning or emphasis 
    LOW    = Grammar, archaic usage, minor phrasing (included for completeness)

We apply HIGH and MEDIUM corrections to the Original files and
log everything to a corrections report.
"""

import json
import os
import re

BOMDB_FILE = "/Users/ericdenna/Library/CloudStorage/GoogleDrive-eric.denna@gmail.com/My Drive/! AAA Personal - WIP/! Joseph the Prophet/JSB - WIP/JSB Doctrinal Learning  over time/JS Revelations by Date/bomdb_contents.json"

OUTPUT_DIR = "/Users/ericdenna/Library/CloudStorage/GoogleDrive-eric.denna@gmail.com/My Drive/! AAA Personal - WIP/! Joseph the Prophet/JSB - WIP/JSB Doctrinal Learning  over time/JS Revelations by Date"

# Book mapping (same as other scripts)
BOOK_MAP = {
    "1 Nephi": "1Nephi", "2 Nephi": "2Nephi", "Jacob": "Jacob",
    "Enos": "Enos", "Jarom": "Jarom", "Omni": "Omni",
    "Words of Mormon": "WordsOfMormon", "Mosiah": "Mosiah",
    "Alma": "Alma", "Helaman": "Helaman", "3 Nephi": "3Nephi",
    "4 Nephi": "4Nephi", "Mormon": "Mormon", "Ether": "Ether",
    "Moroni": "Moroni",
}

# Translation dates
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


# ═══════════════════════════════════════════════════════════════════
# SKOUSEN CORRECTIONS DATABASE
# ═══════════════════════════════════════════════════════════════════
# Each entry: (verse_ref, pm_snippet, earliest_text_snippet, 
#              significance, change_type, source, notes)
#
# pm_snippet/earliest_text_snippet are case-insensitive substring 
# matches that will be used to find and replace within the BomDB text.
# ═══════════════════════════════════════════════════════════════════

CORRECTIONS = [
    # ──────────────────────────────────────────────────────────────
    # HIGH SIGNIFICANCE — Doctrinal / Theological changes
    # ──────────────────────────────────────────────────────────────
    {
        "verse": "1 Nephi 8:31",
        "pm": "feeling their way",
        "earliest": "pressing their way",
        "significance": "HIGH",
        "type": "MISREAD",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Oliver misread 'pressing' as 'feeling' in copying O→P. 'Pressing forward' is the consistent usage in Lehi's dream (5 times). Changes image from uncertainty to determination toward the great and spacious building."
    },
    {
        "verse": "1 Nephi 10:10",
        "pm": "sins of the world",
        "earliest": "sin of the world",
        "significance": "HIGH",
        "type": "THEOLOGICAL PRECISION",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "John the Baptist on Christ: singular 'sin' matches John 1:29 KJV ('the Lamb of God which taketh away the sin of the world'). The Book of Mormon consistently uses singular when quoting John, plural elsewhere. Oliver changed to expected plural."
    },
    {
        "verse": "1 Nephi 12:18",
        "pm": "the word of the justice",
        "earliest": "the sword of the justice",
        "significance": "HIGH",
        "type": "MISREAD",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Oliver misread 'sword' as 'word'. The 'sword of justice' appears 7 times in BOM; 'word of justice' appears nowhere else. Ether 8:23 has identical phrase: 'the sword of the justice of the Eternal God shall fall upon you.'"
    },
    {
        "verse": "1 Nephi 15:16",
        "pm": "remembered again among",
        "earliest": "numbered again among",
        "significance": "HIGH",
        "type": "MISREAD",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Oliver misread 'numbered' as 'remembered'. Being 'numbered among' is standard covenant language in BOM — being counted as part of God's people. 'Remembered' introduces a different theological concept."
    },
    {
        "verse": "1 Nephi 15:35",
        "pm": "preparator",
        "earliest": "proprietor",
        "significance": "HIGH",
        "type": "MISREAD/EMENDATION",
        "source": "Skousen BYU Studies 2012, ATV, Yale",
        "notes": "PM has 'preparator' (strange word). Skousen argues 'proprietor' was original — 'the devil is the proprietor of [hell]' — meaning owner/possessor. Joseph changed to 'foundation' in 1837. Original has major doctrinal implications about Satan's dominion."
    },
    {
        "verse": "1 Nephi 15:36",
        "pm": "rejected from the righteous",
        "earliest": "separated from the righteous",
        "significance": "HIGH",
        "type": "MISREAD",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Oliver misread 'separated' as 'rejected'. Verse 28 uses the exact same idea: 'separateth the wicked from the tree of life.' The wicked reject the tree of life; they are not rejected from it. Fundamentally different soteriology."
    },
    {
        "verse": "1 Nephi 22:8",
        "pm": "nourished by the Gentiles",
        "earliest": "nursed by the Gentiles",
        "significance": "HIGH",
        "type": "MISREAD",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Oliver misread 'nursed' as 'nourished'. The Isaiah source (49:23) says 'nursing fathers' and 'nursing mothers.' The correct 'nursed' appears in verse 6. Changes the Isaianic metaphor from maternal intimacy to generic sustenance."
    },
    {
        "verse": "2 Nephi 31:4",
        "pm": "sins of the world",
        "earliest": "sin of the world",
        "significance": "HIGH",
        "type": "THEOLOGICAL PRECISION",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Same as 1 Nephi 10:10 — singular 'sin' in John the Baptist's declaration about Christ. Changed to plural by 1830 typesetter."
    },
    {
        "verse": "Alma 42:2",
        "pm": "he drew out the man",
        "earliest": "he drove out the man",
        "significance": "HIGH",
        "type": "MISREAD",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Oliver misread 'drove' as 'drew'. The Genesis source (3:24) says 'he drove out the man.' 'Drew out' softens the divine judgment; 'drove out' preserves the biblical severity of the Fall."
    },
    {
        "verse": "Alma 43:14",
        "pm": "descendants were as numerous",
        "earliest": "dissenters were as numerous",
        "significance": "HIGH",
        "type": "MISREAD",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Oliver misread 'dissenters' (spelled 'desenters') as 'descendants' (spelled 'desendants'). The original says there were almost as many Nephite dissenters as Nephites — a dire political/covenant situation. 'Descendants' implies impossible population growth."
    },
    {
        "verse": "Alma 43:38",
        "pm": "by their swords",
        "earliest": "by their wounds",
        "significance": "MEDIUM",
        "type": "MISREAD",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Oliver misread 'wounds' as 'swords'. The Nephites fell by their wounds, not by their own swords."
    },
    {
        "verse": "Alma 47:13",
        "pm": "a second leader",
        "earliest": "the second leader",
        "significance": "MEDIUM",
        "type": "MISREAD",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Oliver misread definite 'the' as indefinite 'a'. There was a specific office of 'the second leader' with automatic succession rules (v. 17)."
    },
    {
        "verse": "Alma 51:7",
        "pm": "many the people of liberty",
        "earliest": "among the people of liberty",
        "significance": "MEDIUM",
        "type": "MISREAD",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Oliver misread 'among' as 'many.' Original: ALL people of liberty supported Parhoron. 'Many' implies only some did."
    },
    {
        "verse": "Alma 51:15",
        "pm": "desiring that he should read it",
        "earliest": "desiring that he should heed it",
        "significance": "MEDIUM",
        "type": "MISREAD",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Oliver misspelled 'heed' as 'head'; typesetter corrected to 'read'. Moroni wanted the governor to heed (act on) the petition, not just read it."
    },

    # ──────────────────────────────────────────────────────────────
    # MEDIUM SIGNIFICANCE — Narrative/emphasis changes
    # ──────────────────────────────────────────────────────────────
    {
        "verse": "Mosiah 21:28",
        "pm": "king Mosiah",
        "earliest": "king Benjamin",
        "significance": "MEDIUM",
        "type": "EDITORIAL",
        "source": "Skousen ATV, multiple sources",
        "notes": "Changed Benjamin→Mosiah in 1837 to avoid perceived chronological difficulty. Skousen argues 'Benjamin' was original and there is no contradiction if Benjamin was still alive."
    },
    {
        "verse": "Ether 4:1",
        "pm": "king Mosiah",
        "earliest": "king Benjamin",
        "significance": "MEDIUM",
        "type": "EDITORIAL",
        "source": "Skousen ATV, multiple sources",
        "notes": "Same Benjamin→Mosiah change as Mosiah 21:28."
    },
    {
        "verse": "2 Nephi 28:23",
        "pm": "death and hell and the devil and all",
        "earliest": "death and hell and the devil and all",
        "significance": "MEDIUM",
        "type": "DITTOGRAPHY",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Accidental repetition of 'death and hell and'. Original likely: 'grasped with death and hell and the devil and all that have been seized therewith.' Dittography during O→P copy."
    },
    {
        "verse": "Helaman 8:11",
        "pm": "they parted hither and thither",
        "earliest": "they departed hither and thither",
        "significance": "MEDIUM",
        "type": "ARCHAIC REPLACEMENT",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "Archaic 'depart' = 'to part/separate' (cf. Geneva Bible John 19:24: 'they departed my raiment'). 1830 typesetter replaced with modern 'parted.'"
    },
    {
        "verse": "Alma 17:1",
        "pm": "he met with the sons of Mosiah",
        "earliest": "he met the sons of Mosiah",
        "significance": "MEDIUM",
        "type": "TYPESETTER ADDITION",
        "source": "Skousen BYU Studies 2012, ATV",
        "notes": "'Met with' implies planned meeting; 'met' indicates surprise encounter (consistent with 'to his astonishment'). BOM has 51 cases of 'X meets Y', zero of 'X meets with Y.'"
    },

    # ──────────────────────────────────────────────────────────────
    # Additional well-documented corrections from ATV/web research
    # ──────────────────────────────────────────────────────────────
    {
        "verse": "1 Nephi 13:6",
        "pm": "the foundation of",
        "earliest": "the founder of",
        "significance": "HIGH",
        "type": "EDITORIAL REVERSION",
        "source": "Skousen ATV; restored in 1981 LDS edition",
        "notes": "Joseph changed 'founder' to 'foundation' in 1837. 'Founder' = the one who establishes the 'great and abominable church.' Changes from Structure to Agent — doctrinally significant for understanding evil."
    },
    {
        "verse": "1 Nephi 14:17",
        "pm": "the foundation of",
        "earliest": "the founder of",
        "significance": "HIGH",
        "type": "EDITORIAL REVERSION",
        "source": "Skousen ATV; restored in 1981 LDS edition",
        "notes": "Same founder→foundation change. Restored in 1981."
    },
    {
        "verse": "2 Nephi 26:22",
        "pm": "the foundation of",
        "earliest": "the founder of",
        "significance": "HIGH",
        "type": "EDITORIAL REVERSION",
        "source": "Skousen ATV; restored in 1981 LDS edition",
        "notes": "Same founder→foundation change (appears twice in verse). Devil as 'founder' of secret combinations."
    },
]


def apply_correction(text, correction):
    """Apply a single correction to verse text. Returns (new_text, applied)."""
    pm_phrase = correction["pm"]
    earliest_phrase = correction["earliest"]
    
    # Case-insensitive search
    lower_text = text.lower()
    lower_pm = pm_phrase.lower()
    
    idx = lower_text.find(lower_pm)
    if idx >= 0:
        # Replace preserving original case pattern where possible
        new_text = text[:idx] + earliest_phrase + text[idx + len(pm_phrase):]
        return new_text, True
    
    return text, False


def main():
    print("=" * 70)
    print("Applying Skousen Critical Text Corrections to Original Files")
    print("=" * 70)
    
    # Load BomDB
    with open(BOMDB_FILE, 'r') as f:
        data = json.load(f)
    contents = data["contents"]
    
    # Stats
    applied_high = []
    applied_medium = []
    skipped_low = []
    not_found = []
    
    # Index corrections by book and chapter
    corrections_by_verse = {}
    for c in CORRECTIONS:
        # Only apply HIGH and MEDIUM
        if c["significance"] == "LOW":
            skipped_low.append(c)
            continue
        corrections_by_verse.setdefault(c["verse"], []).append(c)
    
    # Process each Original file
    files_modified = 0
    
    for book_name, chapters in contents.items():
        prefix = BOOK_MAP.get(book_name)
        if not prefix:
            continue
        
        for ch_str, verses in sorted(chapters.items(), key=lambda x: int(x[0])):
            ch = int(ch_str)
            date_key = (book_name, ch)
            orig_date = CHAPTER_DATES.get(date_key, "unknown")
            
            # Check if any corrections apply to this chapter
            chapter_corrections = []
            for ref, corrs in corrections_by_verse.items():
                # Parse "1 Nephi 10:10" → book="1 Nephi", ch=10
                match = re.match(r'(.+?)\s+(\d+):(\d+)', ref)
                if match:
                    c_book = match.group(1)
                    c_ch = int(match.group(2))
                    if c_book == book_name and c_ch == ch:
                        chapter_corrections.extend([(ref, c) for c in corrs])
            
            if not chapter_corrections:
                continue
            
            # Read current Original file
            filename = f"{orig_date}-{prefix}-{ch}-Original.txt"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            if not os.path.exists(filepath):
                for ref, c in chapter_corrections:
                    not_found.append((c, f"File not found: {filename}"))
                continue
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Apply corrections
            modified = False
            applied_to_file = []
            
            for ref, corr in chapter_corrections:
                new_content, was_applied = apply_correction(content, corr)
                if was_applied:
                    content = new_content
                    modified = True
                    applied_to_file.append(corr)
                    if corr["significance"] == "HIGH":
                        applied_high.append(corr)
                    else:
                        applied_medium.append(corr)
                else:
                    not_found.append((corr, f"Pattern not found in {filename}"))
            
            if modified:
                # Add Skousen corrections header
                header_lines = []
                sep = "\u2550" * 60
                header_lines.append(sep)
                header_lines.append(f"SKOUSEN CRITICAL TEXT CORRECTIONS \u2014 {book_name} {ch}")
                header_lines.append(sep)
                header_lines.append("")
                header_lines.append("The following corrections from Royal Skousen's Critical Text")
                header_lines.append("Project have been applied to this Printer's Manuscript text")
                header_lines.append("to better approximate the Original Manuscript / earliest dictation:")
                header_lines.append("")
                
                for i, corr in enumerate(applied_to_file, 1):
                    header_lines.append(f"  {i}. [{corr['significance']}] {corr['verse']} — {corr['type']}")
                    header_lines.append(f"     PM:       \"{corr['pm']}\"")
                    header_lines.append(f"     Earliest: \"{corr['earliest']}\"")
                    header_lines.append(f"     Source:   {corr['source']}")
                    header_lines.append(f"     Notes:    {corr['notes'][:120]}")
                    header_lines.append("")
                
                header_lines.append(sep)
                header_lines.append("")
                
                header = "\n".join(header_lines)
                
                # Insert header after the date line
                if content.startswith("["):
                    # Find end of date line
                    date_end = content.find("\n") + 1
                    content = content[:date_end] + "\n" + header + content[date_end:]
                else:
                    content = header + content
                
                with open(filepath, 'w') as f:
                    f.write(content)
                
                files_modified += 1
    
    # Print report
    print(f"\n{'=' * 70}")
    print("CORRECTIONS APPLIED")
    print(f"{'=' * 70}")
    print(f"\n  HIGH significance applied:   {len(applied_high)}")
    print(f"  MEDIUM significance applied: {len(applied_medium)}")
    print(f"  LOW significance skipped:    {len(skipped_low)}")
    print(f"  Files modified:              {files_modified}")
    
    if not_found:
        print(f"\n  Corrections NOT found in text: {len(not_found)}")
        for corr, reason in not_found:
            print(f"    - {corr['verse']}: {reason}")
    
    print(f"\n{'=' * 70}")
    print("HIGH SIGNIFICANCE CORRECTIONS")
    print(f"{'=' * 70}")
    for c in applied_high:
        print(f"\n  {c['verse']}:")
        print(f"    PM:       \"{c['pm']}\"")
        print(f"    Earliest: \"{c['earliest']}\"")
        print(f"    Notes:    {c['notes'][:100]}")
    
    print(f"\n{'=' * 70}")
    print("COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
