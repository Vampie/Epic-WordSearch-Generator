"""
Script to generate a complete word search book PDF from a set of puzzles.

This script reads a JSON file containing multiple word search puzzle
definitions, generates each puzzle and its solution, and compiles them into
a single PDF book with a title page, puzzle pages, and solution pages.

Thin wrapper around wordsearch.book_builder, which holds the shared
puzzle-generation and PDF-assembly logic used by both this script and
generate_big_ws_book.py.
"""

import argparse
import json
import os

from wordsearch.book_builder import (
    assemble_book_pdf,
    generate_single_puzzle,
    output_filename,
    resolve_input_path,
    resolve_output_suffix,
)

if __name__ == "__main__":

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="input file, json format")
    parser.add_argument("output", help="output folder")
    parser.add_argument(
        "-n",
        "--name",
        help="name of the output book (without extension)",
        default=None
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

    # If the given input isn't an existing path, try to locate a JSON
    # file with that name anywhere under data/.
    input_path = resolve_input_path(args.input, base_dir="data")

    # Read input data
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    puzzle_name = data.get("title", os.path.splitext(os.path.basename(input_path))[0]).replace(" ", "_").lower()
    if args.name:
        puzzle_name = args.name

    output_dir = args.output
    suffix = resolve_output_suffix(output_dir, puzzle_name, [("book", "pdf")], force=args.force)
    args.output = os.path.join(output_dir, output_filename(puzzle_name, "book", "pdf", suffix))

    puzzles = []
    solutions = []
    puzzle_count = len(data["puzzles"])
    print(f"Generating book with {puzzle_count} puzzles...")

    # Generate puzzles and solutions
    for item in data["puzzles"]:
        size = item.get("size", 15)
        puzzle = generate_single_puzzle(
            item["title"], item["words"], size, use_basic=False, verbose=False,
            max_attempts=8,
        )

        if puzzle is None:
            continue
        puzzles.append((item["title"], puzzle.grid, puzzle.words))
        solutions.append((item["title"], puzzle.grid, puzzle.get_highlights()))

    assemble_book_pdf(
        puzzles,
        solutions,
        args.output,
        puzzle_name,
        puzzle_count=puzzle_count,
        about_content=data.get("description", None),
    )
    print(f"Book PDF generated: {args.output}")
