# Input Type Parameter Usage Guide

The `generate_big_ws_book.py` script now supports two input modes via the `--input-type` parameter.

## Mode 1: Generate New Puzzles (default)

Use `--input-type wordlist` (or omit this parameter) to generate new puzzles from word lists:

```bash
python scripts/generate_big_ws_book.py data/books/01_animals_20_lists.json releases/01 -c 4
```

This will:
1. Generate puzzles from the word lists in the JSON file
2. Save puzzle data to `{puzzle_name}_data.json`
3. Generate the book PDF and cover image

## Mode 2: Regenerate from Existing Puzzle Data

Use `--input-type puzzles` to regenerate a book from previously generated puzzles without changing them:

```bash
python scripts/generate_big_ws_book.py releases/01/animals_20_lists_data.json releases/01_regenerated --input-type puzzles
```

This will:
1. Load the puzzle data from the `_data.json` file
2. Generate the book PDF and cover image using the same puzzles

## Use Cases

### When to use `--input-type wordlist` (default):
- Creating a new word search book for the first time
- Generating different variations of puzzles with the same word lists
- When you want new random puzzle layouts

### When to use `--input-type puzzles`:
- Regenerating a book with the exact same puzzles (e.g., after fixing PDF rendering issues)
- Creating multiple formats of the same puzzles
- Testing PDF layout changes without regenerating puzzles
- Ensuring consistency when you need the exact same puzzles

## Examples

### Example 1: Generate a new book with 4 variations per theme
```bash
python scripts/generate_big_ws_book.py \
    data/books/01_animals_20_lists.json \
    releases/01 \
    -n animals_book \
    -c 4
```

Output:
- `releases/01/animals_book_data.json` (puzzle data)
- `releases/01/animals_book_bigbook.pdf` (the book)
- `releases/01/animals_book_cover.png` (cover image)

### Example 2: Regenerate the book from saved puzzle data
```bash
python scripts/generate_big_ws_book.py \
    releases/01/animals_book_data.json \
    releases/01_v2 \
    --input-type puzzles \
    -n animals_book_v2
```

Output:
- `releases/01_v2/animals_book_v2_bigbook.pdf` (same puzzles, new PDF)
- `releases/01_v2/animals_book_v2_cover.png` (cover image)

Note: The `-c/--copies` parameter is ignored when using `--input-type puzzles` since the puzzles are already generated.

Note: if any of these files already exist in the output folder, they are not overwritten — a shared `_1`, `_2`, ... suffix is added to all of that run's files instead.
