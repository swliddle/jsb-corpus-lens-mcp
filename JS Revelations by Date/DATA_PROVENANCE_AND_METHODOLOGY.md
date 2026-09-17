# Data Provenance and Methodology
## JS Revelations by Date — Book of Mormon Edition Files

**Document Purpose:** This document provides a full audit trail for all Book of
Mormon edition files in this directory. It details every data source, script,
decision, and known limitation so that any researcher can reproduce, verify,
or extend this work.

**Last Updated:** April 20, 2026 (Skousen verification complete)
**Prepared by:** Eric Denna, with engineering assistance from Antigravity AI

---

## 1. Project Overview

This directory contains chapter-level text files for the Book of Mormon
organized by historical date, supporting comparative doctrinal theme analysis
across multiple editions. The project parallels a similar effort completed
for the Doctrine and Covenants, where each revelation is stored by date with
textual change headers documenting differences between editions.

### Scope

- **239 chapters** of the Book of Mormon
- **4 editions** per chapter = **956 total files**
- Each later-edition file includes a **textual change header** documenting
  meaning-altering differences from the preceding edition

### File Naming Convention

```
{DATE}-{BOOK}-{CHAPTER}-{EDITION}.txt
```

- **DATE:** ISO 8601 date (YYYY-MM-DD) associated with that edition
- **BOOK:** Book abbreviation (e.g., 1Nephi, Mosiah, Alma, WordsOfMormon)
- **CHAPTER:** Chapter number (modern chapter divisions)
- **EDITION:** Edition label (Original, 1830, 1837, 1840)

**Examples:**
- `1829-06-05-1Nephi-1-Original.txt` — 1 Nephi 1, Earliest Text (Skousen reconstruction)
- `1830-03-26-1Nephi-1-1830.txt` — 1 Nephi 1, 1830 Palmyra edition
- `1837-02-01-1Nephi-1-1837.txt` — 1 Nephi 1, 1837 Kirtland edition
- `1840-10-03-1Nephi-1-1840.txt` — 1 Nephi 1, 1840 Nauvoo edition

---

## 2. Editions Produced

| Edition | Edition Date | Files | Description |
|---|---|---|---|
| Original (1829 Earliest Text) | Translation dates (Mar–Jun 1829) | 239 | Skousen's Earliest Text reconstruction |
| 1830 Palmyra | 1830-03-26 | 239 | First printed edition |
| 1837 Kirtland | 1837-02-01 | 239 | Joseph Smith's first revision |
| 1840 Nauvoo | 1840-10-03 | 239 | Joseph Smith's second revision |

### Edition Dates Explained

- **Original files** use translation dates per Welch's timeline (see §4 below).
  These represent when the text was originally dictated, not when the PM was
  copied. The Printer's Manuscript was produced in Aug–Sep 1829.
- **1830-03-26** is the publication date of the first edition in Palmyra, NY.
- **1837-02-01** is the approximate publication date of the Kirtland edition.
- **1840-10-03** is the approximate publication date of the Nauvoo edition.

---

## 3. Primary Data Source: BomDB (Wordtree Foundation)

### Source

- **Repository:** https://github.com/wordtreefoundation/bomdb
- **Data file:** `data/contents.json` (raw URL: https://raw.githubusercontent.com/wordtreefoundation/bomdb/master/data/contents.json)
- **License:** MIT License
- **Local copy:** `bomdb_contents.json` in this directory

### What BomDB Contains

BomDB is a scholarly, open-source, verse-aligned database of the Book of
Mormon containing the following editions:

| BomDB Key | Edition Name | Our Usage |
|---|---|---|
| `1829` | 1829 Earliest Text (Skousen reconstruction) | → **Original** files |
| `1830` | 1830 Palmyra | → **1830** files |
| `1837` | 1837 Kirtland | → **1837** files |
| `1840` | 1840 Nauvoo | → **1840** files |
| `1992` | 1992 Salt Lake City | Not used (modern; outside scope) |

### Data Format

The `contents.json` file is structured as:
```json
{
  "editions": { ... },
  "contents": {
    "1 Nephi": {
      "1": {
        "1 Nephi 1:1": {
          "1829": "I Nephi having been born...",
          "1830": "I, Nephi, having been born...",
          "1837": "I, Nephi, having been born...",
          "1840": "I, Nephi, having been born...",
          "1992": "I, Nephi, having been born..."
        }
      }
    }
  }
}
```

Every verse is aligned across all editions, enabling automated comparison.

### BomDB Data Provenance

According to the BomDB documentation and our independent verification:
- The **1829 text** is derived from Royal Skousen's critical text work.
  Although BomDB labels it "Printer's Manuscript," our verification (see §8)
  confirmed it is actually Skousen's **Earliest Text reconstruction** — the
  PM corrected with OM readings and critical emendations. All 19 of Skousen's
  most significant corrections (BYU Studies 2012) are already incorporated.
- The **1830 text** is from the first edition published by E.B. Grandin in
  Palmyra, NY.
- The **1837 text** is from the second edition published by Parley P. Pratt
  and John Goodson in Kirtland, OH, with revisions by Joseph Smith.
- The **1840 text** is from the third edition published by Ebenezer Robinson
  and Don Carlos Smith in Nauvoo, IL, with revisions by Joseph Smith.

---

## 4. Secondary Data Source: Project Gutenberg (Superseded)

### Source

- **URL:** https://www.gutenberg.org/ebooks/17
- **Title:** *The Book of Mormon* (1830 edition)
- **Format:** Plain text (UTF-8)
- **License:** Public domain

### Usage

The Gutenberg 1830 text was used as the initial data source during the pilot
phase (1 Nephi extraction) before BomDB was discovered. All Gutenberg-based
files have since been **overwritten** by BomDB data.

The Gutenberg text was used to:
1. Establish the extraction pipeline and file format
2. Validate the chapter-to-date mapping
3. Pilot the 1 Nephi extraction

**All 956 production files now use BomDB data exclusively.**

---

## 5. Translation Date Mapping

### Source

The translation dates assigned to Original files are based on John W. Welch's
reconstruction of the Book of Mormon translation timeline:

- **Welch, John W.** "How Long Did It Take to Translate the Book of Mormon?"
  *Ensign*, January 1988.
- **Welch, John W. and Tim Rathbone.** "The Translation of the Book of
  Mormon: Basic Historical Information." FARMS Research Report, 1986.

### Method

Welch estimates approximately 63–65 working translation days between
April 7, 1829 and June 30, 1829 (after Oliver Cowdery arrived as scribe).
The translation order followed what scholars call the "Mosiah Priority"
sequence:

1. **Mosiah → Moroni** (Mosiah 1 through Moroni 10): April 7 – May 31, 1829
2. **1 Nephi → Words of Mormon** (1 Nephi 1 through Words of Mormon 1):
   June 1 – June 30, 1829

Chapter-to-date assignments were distributed proportionally based on
chapter length within each translation session, cross-referenced with
historical data about days lost to other activities (e.g., May 15
baptism, May 18–19 visiting relatives).

### Complete Translation Date Mapping

The mapping is encoded in the Python scripts (see §7). Key landmarks:

| Date | Content |
|---|---|
| 1829-03-31 | Mosiah 1 (116 pp. lost; Mosiah is beginning of extant dictation) |
| 1829-04-07 | Mosiah 2–4 (Oliver Cowdery arrives as scribe) |
| 1829-05-04 | Alma 62–63, Helaman 1 |
| 1829-05-15 | (Aaronic Priesthood restoration — no translation) |
| 1829-05-31 | Moroni 9–10 (end of Mosiah-priority sequence) |
| 1829-06-05 | 1 Nephi 1–2 (begins re-translation of small plates) |
| 1829-06-28 | Omni 1, Words of Mormon 1 (final translation day) |

### Known Limitations

- Welch's timeline is an **approximation**. Exact daily boundaries are
  uncertain. Chapter assignments within a given day are estimated.
- The March 31 date for Mosiah 1 accounts for early translation work
  before Cowdery (Martin Harris as scribe, lost 116 pages period).
- Some scholars propose slightly different timelines; our dates represent
  the mainstream LDS scholarly consensus as of 2026.

---

## 6. Textual Change Detection Methodology

### How Changes Are Identified

Each edition file (1830, 1837, 1840) contains a header documenting textual
changes from the previous edition. The detection algorithm:

1. **Verse alignment:** BomDB provides pre-aligned verses across editions.
2. **Exact match check:** If verse text is character-for-character identical,
   no change is recorded.
3. **Punctuation/capitalization filter:** If the only differences are in
   punctuation or capitalization, the change is excluded (not "meaning-
   altering").
4. **Word-level comparison:** After removing punctuation, verses are split
   into word lists. Changes in the word sets indicate meaningful changes.
5. **Classification:** Changes are classified as:
   - `WORD CHANGE` — typical substitution/insertion/deletion
   - `PHRASE ADDITION` — later edition is significantly longer (>30%)
   - `PHRASE REMOVAL` — later edition is significantly shorter (>30%)

### Change Chain

Each edition is compared only against its **immediate predecessor**:

```
Original (1829 PM) → 1830 Palmyra → 1837 Kirtland → 1840 Nauvoo
                    (2,355 changes)  (2,464 changes)  (492 changes)
```

**Total changes detected across all editions: 5,311**

### Known Limitations of Change Detection

- The filter is intentionally conservative. Some punctuation changes that
  **do** alter meaning (e.g., period vs. semicolon affecting sentence
  boundaries) may be filtered out.
- The algorithm compares **word sets** rather than word sequences, so some
  word-order changes may not be detected.
- Very long verses with many changes may have truncated display in headers
  (capped at 150 characters per line in the EARLIER/LATER display).
- The BomDB data itself may contain minor transcription inaccuracies
  (e.g., `was0` appears in one verse of the 1837 data — likely a typo).

---

## 7. Scripts Used

All scripts are Python 3 and are located in this directory. They are
listed in the order they were created and executed.

### Phase 1: Pilot Extraction (Gutenberg-based, now superseded)

| Script | Purpose | Status |
|---|---|---|
| `bom_1nephi_extract.py` | Pilot extraction of 1 Nephi from Gutenberg | Superseded |
| `bom_full_extract.py` | Full extraction of all books from Gutenberg | Superseded |
| `bom_4nephi_fix.py` | Fix for 4 Nephi (non-standard Gutenberg format) | Superseded |
| `bom_singlechapter_fix.py` | Fix for Enos, Jarom, Omni, Words of Mormon | Superseded |
| `bom_add_diff_headers.py` | Add placeholder diff headers to 1830 files | Superseded |

### Phase 2: Production Extraction (BomDB-based, current)

| Script | Purpose | Status |
|---|---|---|
| `bom_multiedition_extract.py` | Generate 1837 & 1840 edition files from BomDB | **Active** |
| `bom_upgrade_original_1830.py` | Upgrade Original & 1830 files with BomDB data | **Active** |
| `bom_skousen_corrections.py` | Verify/apply Skousen corrections (all pre-applied) | **Verification** |

### How to Reproduce

To regenerate all files from scratch:

```bash
# 1. Ensure bomdb_contents.json is present in this directory
#    (downloaded from https://raw.githubusercontent.com/wordtreefoundation/bomdb/master/data/contents.json)

# 2. Generate Original (PM) and 1830 files with real diff headers
python3 bom_upgrade_original_1830.py

# 3. Generate 1837 and 1840 files with diff headers
python3 bom_multiedition_extract.py
```

Both scripts are idempotent — they overwrite existing files with fresh output.

---

## 8. Skousen Critical Text Integration — VERIFIED COMPLETE

### Key Finding

On April 20, 2026, we systematically verified that the BomDB "1829" text
is NOT the raw Printer's Manuscript — it is Royal Skousen's **Earliest Text
reconstruction**. This means our Original files already incorporate Skousen's
critical corrections at the data-source level.

### Verification Method

We tested all 19 of Skousen's most significant corrections (from his 2012
BYU Studies article) against the BomDB 1829 text:

| # | Verse | PM Reading | Earliest Text | Status |
|---|---|---|---|---|
| 1 | 1 Nephi 8:31 | feeling their way | **pressing** their way | ✅ Already correct |
| 2 | 1 Nephi 10:10 | sin**s** of the world | **sin** of the world | ✅ Already correct |
| 3 | 1 Nephi 12:18 | the **word** of the justice | the **sword** of the justice | ✅ Already correct |
| 4 | 1 Nephi 13:6 | the **foundation** of | the **founder** of | ✅ Already correct |
| 5 | 1 Nephi 14:17 | the **foundation** of | the **founder** of | ✅ Already correct |
| 6 | 1 Nephi 15:16 | **remembered** again | **numbered** again | ✅ Already correct |
| 7 | 1 Nephi 15:35 | **preparator** | **proprietor** | ✅ Already correct |
| 8 | 1 Nephi 15:36 | **rejected** from | **separated** from | ✅ Already correct |
| 9 | 1 Nephi 22:8 | **nourished** by | **nursed** by | ✅ Already correct |
| 10 | 2 Nephi 26:22 | the **foundation** of | the **founder** of | ✅ Already correct |
| 11 | 2 Nephi 31:4 | sin**s** of the world | **sin** of the world | ✅ Already correct |
| 12 | Mosiah 21:28 | king **Mosiah** | king **Benjamin** | ✅ Already correct |
| 13 | Alma 42:2 | he **drew** out the man | he **drove** out the man | ✅ Already correct |
| 14 | Alma 43:14 | **descendants** were | **dissenters** were | ✅ Already correct |
| 15 | Alma 43:38 | by their **swords** | by their **wounds** | ✅ Already correct |
| 16 | Alma 47:13 | **a** second leader | **the** second leader | ✅ Already correct |
| 17 | Alma 51:7 | **many** the people | **among** the people | ✅ Already correct |
| 18 | Helaman 8:11 | they **parted** | they **departed** | ✅ Already correct |
| 19 | Ether 4:1 | king **Mosiah** | king **Benjamin** | ✅ Already correct |

**Result: 19/19 (100%) of Skousen's most significant corrections are
already present in the BomDB 1829 text.**

### Royal Skousen's Critical Text Project (Background)

Royal Skousen has spent 30+ years reconstructing the "earliest text" of the
Book of Mormon through the Critical Text Project at BYU:

1. **The Original Manuscript of the Book of Mormon** (FARMS, 2001) —
   Typographical facsimile of surviving OM fragments (~28% extant).
2. **The Printer's Manuscript of the Book of Mormon** (2 vols., FARMS, 2001) —
   Complete typographical facsimile of the PM.
3. **Analysis of Textual Variants of the Book of Mormon** (6 parts,
   FARMS/BYU, 2004–2009) — Verse-by-verse analysis of every textual variant.
   Identifies 256 meaning-altering changes and catalogs 5,000+ total variants.
4. **The Book of Mormon: The Earliest Text** (Yale University Press, 2009;
   2nd ed. 2022) — Reconstructed "earliest text" with appendix of 724
   significant textual variants.

Source for the 19 corrections verified above:
- Skousen, Royal. "Some Textual Changes for a Scholarly Study of the Book
  of Mormon." *BYU Studies Quarterly* 51, no. 4 (2012): 99–117.

### Doctrinal Significance Categories

Skousen's 256 meaning-altering changes fall into several categories:
- **Scribal misreads** (O→P): e.g., "sword"→"word", "nursed"→"nourished"
- **Singular/plural errors**: e.g., "sin"→"sins" (Johannine theology)
- **Archaic replacements**: e.g., "departed"→"parted", "but if"→"unless"
- **Editorial overcorrections**: e.g., "founder"→"foundation" (1837)
- **Name errors**: e.g., "Benjamin"→"Mosiah" (1837, perceived anachronism)

### Remaining Verification Opportunity

The Yale appendix lists 724 total significant variants. Our verification
covered the 19 most significant from Skousen's own curated selection.
The remaining ~700 variants are likely also incorporated (given the 100%
hit rate), but a complete verification against the Yale appendix would
confirm this definitively. This can be done in a future VitalSource
paging session.

### Verification Script

The verification was performed by `bom_skousen_corrections.py`, which
contains the complete corrections database with verse references, PM and
Earliest Text readings, significance ratings, source citations, and
scholarly notes for each correction.

---

## 9. Editions Not Yet Produced

### 1841 Liverpool Edition

- **Published:** February 1841, by Brigham Young, Heber C. Kimball, and
  Parley P. Pratt in Liverpool, England.
- **Status:** Not yet extracted.
- **Basis:** The 1841 edition was set from the 1837 Kirtland edition, not
  the 1840 Nauvoo edition. It has minor differences from both.
- **BomDB status:** BomDB does not include the 1841 edition in its
  `contents.json` (editions available: 1829, 1830, 1837, 1840, 1992).
- **Potential source:** The Joseph Smith Papers have the 1841 edition
  transcribed at https://www.josephsmithpapers.org/paper-summary/book-of-mormon-1841/1.
  Extraction would require page-by-page scraping of the JSP transcript.

### Later Editions (1849, 1879, 1920, 1981, 2013)

These are outside the current scope of the Joseph Smith–era doctrinal
analysis but could be added using BomDB (which has 1992) or JSP sources.

---

## 10. Related Project Context

### Doctrine and Covenants Files

This directory also contains D&C revelation files following the same
date-based naming pattern. Those files were extracted from the Joseph Smith
Papers' Correspondence Table and include similar textual change headers
across the 1833 Book of Commandments, 1835 D&C, and later editions.

### Doctrinal Theme Analysis Pipeline

The files in this directory serve as input to the automated doctrinal
theme analysis pipeline (see `run-daily-revelations-doctrinal-themes.py`
in the parent directory). That script:
1. Reads revelation/translation files by date
2. Sends text to dual AI analysis (Gemini + Claude)
3. Generates doctrinal theme analyses focused on textual changes
4. Stores results in the Doctrinal Themes Analyses Files directory

---

## 11. Audit Checklist

For anyone verifying this work, the following checks can confirm integrity:

- [ ] **File count:** 239 Original + 239 1830 + 239 1837 + 239 1840 = **956 files**
- [ ] **BomDB source:** `bomdb_contents.json` matches the Wordtree Foundation
      repository (SHA hash or re-download to verify)
- [ ] **Verse coverage:** Each chapter file should contain all verses for that
      chapter as listed in the 1992 modern versification
- [ ] **Diff headers:** 1830 files show PM→1830 changes; 1837 files show
      1830→1837 changes; 1840 files show 1837→1840 changes
- [ ] **Translation dates:** Spot-check against Welch (1988) for key chapters
- [ ] **Scripts reproducible:** Running `bom_upgrade_original_1830.py` and
      `bom_multiedition_extract.py` regenerates identical output
- [ ] **No data fabrication:** All verse text traces to BomDB; no text was
      composed, interpolated, or editorially modified
- [ ] **Skousen verification:** Confirm that BomDB 1829 includes Earliest Text
      corrections by spot-checking against Yale appendix (19/19 verified)

---

## 12. Contact and Attribution

- **Project:** Joseph the Prophet — Doctrinal Learning Over Time
- **Author:** Eric Denna
- **AI Engineering:** Antigravity (Google DeepMind)
- **Date Range:** April 2026
- **License:** Research use. BomDB source data is MIT licensed.
  Project Gutenberg text is public domain.
