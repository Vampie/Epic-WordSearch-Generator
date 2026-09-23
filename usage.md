# Usage Guide

Practical reference for the four scripts in [`scripts/`](scripts/). All commands
are run from the repository root, after installing the package:

```bash
pip install -e .
```

## Overview

| Script | Use it when you want to... |
|---|---|
| [`generate_ws_page.py`](scripts/generate_ws_page.py) | Generate one or more standalone puzzle pages (PDF and/or DOCX) |
| [`generate_ws_book.py`](scripts/generate_ws_book.py) | Generate a single complete PDF book from a fixed list of puzzles |
| [`generate_big_ws_book.py`](scripts/generate_big_ws_book.py) | Generate a large PDF book with several randomized variations per theme, plus a cover image and optional HTML blurb |
| [`validate_books.py`](scripts/validate_books.py) | Check that a JSON puzzle file (or a folder of them) is well-formed before feeding it to any of the generators |

All puzzle generation goes through [`src/wordsearch/book_builder.py`](src/wordsearch/book_builder.py),
which is what keeps the three generator scripts thin and consistent with
each other. You don't need to touch it directly to use the CLI.

**Output naming:** every generated file follows the pattern
`<name>_<type>.<ext>` (e.g. `animals_book.pdf`, `animals_cover.png`). If a
file with that exact name already exists in the output folder, it is never
overwritten — a numeric suffix is added instead (`animals_book_1.pdf`,
`animals_book_2.pdf`, ...). When one run produces several related files
(e.g. a big book's PDF, cover, data JSON, and description), they all share
the same suffix, so a set from one run is easy to tell apart from another.

---

## 1. Single puzzle pages — `generate_ws_page.py`

For one-off pages, worksheets, or when you just want PDF/DOCX output per
puzzle rather than a bound book.

```bash
python -m scripts.generate_ws_page data/input_page.json -o output/ --pdf --docx
```

**Arguments:**

- `input` (positional) — JSON file with puzzle definitions (see format below)
- `-o, --output` — output folder (required if `--pdf` and/or `--docx` is used)
- `-b, --basic` — restrict word placement to horizontal (left-to-right),
  vertical (top-to-bottom) and one diagonal direction only
- `--pdf` — write a PDF per puzzle
- `--docx` — write a DOCX per puzzle

**Input JSON format:**

```json
{
    "puzzles": [
        {
            "title": "Animals",
            "words": ["ELEPHANT", "GIRAFFE", "KANGAROO"],
            "size": 18
        }
    ]
}
```

**Output:** one `<title>_wordsearch.pdf` and/or `.docx` file per puzzle in
the output folder, each including the solution. Re-running with the same
titles adds `_1`, `_2`, ... instead of overwriting previous files.

---

## 2. Complete puzzle book — `generate_ws_book.py`

For a fixed, one-shot puzzle book: title/intro pages, one puzzle per page,
then a solutions section at the back.

```bash
python -m scripts.generate_ws_book data/input_book.json output/ -n my_book
```

**Arguments:**

- `input` (positional) — JSON file with puzzles and a root-level `title`
- `output` (positional) — output **folder** (the PDF filename is derived
  automatically)
- `-n, --name` — override the output filename (without extension); defaults
  to the JSON's `title`

**Input JSON format:** same puzzle format as above, with a book `title` (and
optionally a `description`) at the root:

```json
{
    "title": "Animals",
    "description": ["Jungle Animals", "Ocean Animals", "Farm Animals"],
    "puzzles": [
        { "title": "Jungle Animals", "words": ["TIGER", "MONKEY"], "size": 16 }
    ]
}
```

**Output:** `output/<name>_book.pdf` — one PDF containing every puzzle
exactly as listed, in order, followed by all solutions (4 per page).

Use this when you have a curated, final list of puzzles and don't need
random variations.

---

## 3. Large book with variations — `generate_big_ws_book.py`

For bulk-generating a themed book (e.g. a KDP-style puzzle book) where each
theme should produce several different randomized puzzles.

```bash
python -m scripts.generate_big_ws_book data/books/01_animals_20_lists.json output/ -n animals_book -c 4 --pdf -d
```

**Arguments:**

- `input` (positional) — JSON file (word lists, or a previously generated
  puzzle-data file — see `-t`)
- `output` (positional) — output **folder**
- `-n, --name` — output filename (without extension)
- `-c, --copies` — number of randomized variations per theme (default: 4)
- `-t, --input-type` — `wordlist` (default, generates new puzzles from word
  lists) or `puzzles` (reuses previously generated puzzle data — see below)
- `-d, --html-description` — also write a `<name>-description.html` blurb
  with the book's title and category preview

**Input JSON format:** up to 20 themes are used; each theme can set an
optional `count` (how many words to randomly sample per variation) and the
root can set a `color` (hex, used for the cover) and `catchphrase`:

```json
{
    "title": "Animal",
    "color": "#1E90FF",
    "catchphrase": "Hours of fun for animal lovers!",
    "puzzles": [
        {
            "title": "Jungle Animals",
            "words": ["TIGER", "MONKEY", "GORILLA", "..."],
            "size": 16,
            "count": 24
        }
    ]
}
```

**Output** (all written to the output folder):

- `<name>_book.pdf` — the full book (variations, e.g. "Jungle Animals 1",
  "Jungle Animals 2", ...)
- `<name>_data.json` — the generated puzzles/solutions, so the same exact
  puzzles can be reused later (see `-t puzzles` below) without re-rolling
  the randomization
- `<name>_cover.png` — a cover image built from the first puzzle
- `<name>_description.html` — only when `-d` is passed

Re-running with the same `-n`/name never overwrites a previous run: all
four files get the same `_1`, `_2`, ... suffix instead.

**Reusing a previously generated book** (e.g. to regenerate the PDF after
tweaking cover color or without re-randomizing puzzles):

```bash
python -m scripts.generate_big_ws_book output/animals_book_data.json output/ -t puzzles -n animals_book_v2
```

Word placement may occasionally fail for a few long/awkward words; the
script retries each puzzle up to 8 times and prints a warning if some words
still couldn't be placed after all attempts — check the console output.

---

## 4. Validating JSON input — `validate_books.py`

Run this before generating a book, especially for hand-edited or large JSON
files, to catch structural mistakes early.

```bash
# Validate a single file
python -m scripts.validate_books data/books/01_animals_20_lists.json

# Validate every .json file in a folder (recursively)
python -m scripts.validate_books data/books/
```

**Checks include:** presence of `title`/`puzzles`, valid `version`-gated
fields (`color` must be a valid hex code, `catchphrase` must be a string
from version 1.1+), duplicate words within a puzzle, and words that don't
fit within the puzzle's `size`.

Exits with code `0` if everything passes, `2` if any file fails validation.

---

## Typical workflow

1. Write or edit your word lists as JSON (see `data/input_page.json`,
   `data/input_book.json`, or `data/books/*.json` for examples).
2. Validate: `python -m scripts.validate_books data/books/your_file.json`
3. Generate:
   - Quick preview of a single puzzle → `generate_ws_page.py`
   - Small, fixed book → `generate_ws_book.py`
   - Large book with variations, cover art, and a web blurb →
     `generate_big_ws_book.py`
4. For a big book you plan to revisit, keep the generated `*_data.json`
   around and pass `-t puzzles` next time instead of regenerating puzzles
   from scratch.
