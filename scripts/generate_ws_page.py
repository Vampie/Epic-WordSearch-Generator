"""
Script to generate word search puzzles from JSON input files.

This module provides a command-line interface for creating wordsearch puzzles
using the wordsearch library. It accepts JSON files containing puzzle
definitions and outputs the generated puzzles to the console.
"""

import argparse
import json
import logging
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

# pylint: disable=wrong-import-position,import-error
from wordsearch.book_builder import (
    generate_single_puzzle,
    output_filename,
    resolve_input_path,
    resolve_output_suffix,
)
from wordsearch import docx_export
from wordsearch import pdf_render

# Maximum number of words per puzzle, and how many times the grid may grow
# to try to fit all of them before giving up
MAX_WORDS = 40
MAX_SIZE_GROWTH = 10

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

if __name__ == "__main__":

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="input file, json format")
    parser.add_argument("output", help="output folder")
    parser.add_argument(
        "-b",
        "--basic",
        action="store_true",
        help=(
            "only basic directions: left to right, top to bottom, "
            "diagonal from top left to bottom right"
        ),
    )
    parser.add_argument(
        "--docx", action="store_true", help="also generate DOCX output (PDF is always generated)"
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help=(
            "overwrite the final output files instead of adding a _1/_2/... "
            "suffix, and remove any previously generated numbered versions"
        ),
    )
    args = parser.parse_args()

    # If the given input isn't an existing path, try to locate a JSON file
    # with that name anywhere under data/.
    input_path = resolve_input_path(args.input, base_dir="data")

    # get input file data
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logging.error("Failed to read input file: %s", e)
        sys.exit(1)

    # Base name shared by every puzzle from this file: the JSON's own
    # "title" if set, otherwise the input filename.
    book_name = (
        data.get("title", os.path.splitext(os.path.basename(input_path))[0])
        .replace(" ", "_")
        .lower()
    )

    for j, item in enumerate(data["puzzles"]):

        # default size
        size = 15
        puzzle = None

        words = item["words"]
        if len(words) > MAX_WORDS:
            words = words[:MAX_WORDS]

        if {"title", "words"} <= item.keys():
            if "size" in item:
                size = item["size"]

            puzzle = generate_single_puzzle(
                item["title"],
                words,
                size,
                use_basic=args.basic,
                verbose=True,
            )
            # Grow the grid if some words didn't fit, capped to avoid runaway sizes
            growth = 0
            while puzzle.failed_words and growth < MAX_SIZE_GROWTH:
                size += 1
                growth += 1
                puzzle = generate_single_puzzle(
                    item["title"],
                    words,
                    size,
                    use_basic=args.basic,
                    verbose=True,
                )

        if puzzle is None:
            logging.error("Failed to generate puzzle for %s", item["title"])
            continue

        # Get highlights for the solution
        highlights = puzzle.get_highlights()

        puzzle_doc_type = item["title"].lower().replace(" ", "_")
        wanted_outputs = [(puzzle_doc_type, "pdf")]
        if args.docx:
            wanted_outputs.append((puzzle_doc_type, "docx"))
        suffix = resolve_output_suffix(args.output, book_name, wanted_outputs, force=args.force)

        # Save PDF with grid and solution (always generated)
        output_pdf = output_filename(book_name, puzzle_doc_type, "pdf", suffix)
        output_pdf = os.path.join(args.output, output_pdf)
        pdf_render.render_wordsearch_pdf(
            output_pdf, item["title"], puzzle.grid, puzzle.words, highlights, None
        )

        if args.docx:
            # Save DOCX with grid and solution
            output_docx = output_filename(book_name, puzzle_doc_type, "docx", suffix)
            output_docx = os.path.join(args.output, output_docx)
            docx_export.save_wordsearch_to_docx(
                output_docx, item["title"], puzzle.grid, puzzle.words, highlights
            )
