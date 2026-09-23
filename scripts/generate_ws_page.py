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
    parser.add_argument("-o", "--output", help="output folder")
    parser.add_argument(
        "-b",
        "--basic",
        action="store_true",
        help=(
            "only basic directions: left to right, top to bottom, "
            "diagonal from top left to bottom right"
        ),
    )
    parser.add_argument("--pdf", action="store_true", help="generate PDF output")
    parser.add_argument("--docx", action="store_true", help="generate DOCX output")
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

    # get input file data
    input_file = os.path.join(os.getcwd(), args.input)
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logging.error("Failed to read input file: %s", e)
        sys.exit(1)

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

        puzzle_base_name = item["title"].lower().replace(" ", "_")
        wanted_outputs = []
        if args.docx:
            wanted_outputs.append(("wordsearch", "docx"))
        if args.pdf:
            wanted_outputs.append(("wordsearch", "pdf"))
        suffix = None
        if wanted_outputs and args.output:
            suffix = resolve_output_suffix(args.output, puzzle_base_name, wanted_outputs, force=args.force)

        if args.docx:
            if not args.output:
                logging.error("Output folder must be specified for DOCX output")
                continue
            # Save DOCX with grid and solution
            output_docx = output_filename(puzzle_base_name, "wordsearch", "docx", suffix)
            output_docx = os.path.join(args.output, output_docx)
            docx_export.save_wordsearch_to_docx(
                output_docx, item["title"], puzzle.grid, puzzle.words, highlights
            )

        if args.pdf:
            if not args.output:
                logging.error("Output folder must be specified for PDF output")
                continue
            # Save PDF with grid and solution
            output_pdf = output_filename(puzzle_base_name, "wordsearch", "pdf", suffix)
            output_pdf = os.path.join(args.output, output_pdf)
            pdf_render.render_wordsearch_pdf(
                output_pdf, item["title"], puzzle.grid, puzzle.words, highlights, None
            )
