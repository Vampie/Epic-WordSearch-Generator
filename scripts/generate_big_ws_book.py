"""
Script to generate a large word search book PDF from a set of puzzles.

This script reads a JSON file containing multiple word search puzzle
definitions, generates several variations of each puzzle, and compiles them
into a single PDF book with a title page, puzzle pages, and solution pages.
Each puzzle definition results in N unique puzzles (e.g., "Jungle Animals 1",
"Jungle Animals 2", "Jungle Animals 3", "Jungle Animals 4").

Thin wrapper around wordsearch.book_builder, which holds the shared
puzzle-generation and PDF-assembly logic used by both this script and
generate_ws_book.py.
"""

import argparse
import json
import os
import random

from wordsearch import cover_image
from wordsearch.book_builder import assemble_book_pdf, generate_single_puzzle
from wordsearch.html_export import generate_html_description


def save_puzzle_data_to_json(
    puzzles,
    solutions,
    output_path,
    puzzle_name,
    cover_color,
    content_descriptions=None
    ):
    """
    Saves the generated puzzles and solutions to a JSON file with metadata.
    """
    puzzle_data = {
        "metadata": {
            "title": puzzle_name,
            "color": cover_color
        },
        "puzzles": [],
        "solutions": []
    }

    for title, grid, words in puzzles:
        puzzle_data["puzzles"].append({
            "title": title,
            "grid": grid,
            "words": words
        })

    for title, grid, highlights in solutions:
        puzzle_data["solutions"].append({
            "title": title,
            "grid": grid,
            "highlights": highlights
        })

    if content_descriptions:
        puzzle_data["metadata"]["content_descriptions"] = content_descriptions

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(puzzle_data, f, indent=4)


def load_puzzle_data_from_json(input_path):
    """
    Loads previously generated puzzles and solutions from a JSON file.
    Returns: (puzzles, solutions, puzzle_name, cover_color)
    """
    with open(input_path, "r", encoding="utf-8") as f:
        puzzle_data = json.load(f)

    # Extract metadata
    metadata = puzzle_data.get("metadata", {})
    puzzle_name = metadata.get("title", "wordsearch_book")
    cover_color = metadata.get("color", "#1E90FF")

    # Reconstruct puzzles list
    puzzles = []
    for p in puzzle_data["puzzles"]:
        puzzles.append((p["title"], p["grid"], p["words"]))

    # Reconstruct solutions list
    solutions = []
    for s in puzzle_data["solutions"]:
        solutions.append((s["title"], s["grid"], s["highlights"]))

    return puzzles, solutions, puzzle_name, cover_color


if __name__ == "__main__":

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="input file, json format")
    parser.add_argument("output", help="output folder")
    parser.add_argument(
        "-n",
        "--name",
        help="name of the output book (without extension)",
        default=None,
    )
    parser.add_argument(
        "-c",
        "--copies",
        type=int,
        help="number of copies per puzzle (default: 4)",
        default=4,
    )
    parser.add_argument(
        "-t",
        "--input-type",
        choices=["wordlist", "puzzles"],
        default="wordlist",
        help="type of input file: 'wordlist' for puzzle definitions (generates new puzzles), 'puzzles' for previously generated puzzle data (reuses puzzles)",
    )
    parser.add_argument(
        "-d",
        "--html-description",
        action="store_true",
        help="generate an HTML file with the title and description of the book",
    )

    args = parser.parse_args()

    output_dir = args.output
    puzzles = []
    solutions = []
    cover_color = "#1E90FF"  # default blue
    content_descriptions = []
    categories_data = []  # List of (title, [words]) tuples for HTML description
    data = {}

    if args.input_type == "puzzles":
        # Load previously generated puzzle data
        print(f"Loading puzzle data from {args.input}...")
        puzzles, solutions, puzzle_name, cover_color = load_puzzle_data_from_json(args.input)

        # Override puzzle name if specified
        if args.name:
            puzzle_name = args.name

        # get content descriptions from metadata if available
        with open(args.input, "r", encoding="utf-8") as f:
            puzzle_data = json.load(f)
            metadata = puzzle_data.get("metadata", {})
            content_descriptions = metadata.get("content_descriptions", [])

        print(f"Loaded {len(puzzles)} puzzles from data file")

    else:
        # Generate new puzzles from word lists (original behavior)
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)

        puzzle_name = (
            data.get("title", os.path.splitext(os.path.basename(args.input))[0])
            .replace(" ", "_")
            .lower()
        )
        if args.name:
            puzzle_name = args.name

        base_puzzle_count = len(data["puzzles"])
        total_puzzle_count = base_puzzle_count * args.copies
        print(
            f"Generating book with {total_puzzle_count} puzzles "
            f"({base_puzzle_count} themes × {args.copies} variations)..."
        )

        # Get cover color from the json, default to blue
        cover_color = data.get("color", "#1E90FF")

        # Generate puzzles and solutions - create multiple variations for
        # each theme
        for item in data["puzzles"][:20]:
            size = item.get("size", 15)
            count = item.get("count", 20)
            base_title = item["title"]

            # Append the puzzle "title" to descriptions, only first 6 titles
            if len(content_descriptions) < 6:
                content_descriptions.append(base_title)

            # Collect first 7 categories with their first 4 words for HTML description
            if len(categories_data) < 7:
                first_4_words = item["words"][:4]
                categories_data.append((base_title, first_4_words))

            # Generate multiple variations of each puzzle
            for variation in range(1, args.copies + 1):
                # pick a different random list of `count` words from
                # item["words"]; if there are not enough words, take them all
                if len(item["words"]) <= count:
                    selected_words = item["words"]
                else:
                    selected_words = random.sample(item["words"], count)

                puzzle = generate_single_puzzle(
                    base_title, selected_words, size,
                    use_basic=False, verbose=False, max_attempts=8,
                )

                if puzzle is None:
                    continue

                # Add variation number to title
                numbered_title = f"{base_title} {variation}"
                puzzles.append((numbered_title, puzzle.grid, puzzle.words))
                solutions.append(
                    (numbered_title, puzzle.grid, puzzle.get_highlights())
                )

        print(f"Successfully generated {len(puzzles)} puzzles")

        # Save JSON with puzzles and solutions
        save_puzzle_data_to_json(
            puzzles, solutions,
            os.path.join(output_dir, f"{puzzle_name}_data.json"),
            puzzle_name,
            cover_color,
            content_descriptions
        )
        print(f"JSON saved: {os.path.join(output_dir, f'{puzzle_name}_data.json')}")

    pdf_output_path = os.path.join(output_dir, f"{puzzle_name}_book.pdf")

    # generate the cover image in the output folder only for the first puzzle
    cover_image_path = os.path.join(
        output_dir, f"{puzzle_name}_cover_grid.png"
    )

    cover_image.render_wordsearch_cover(
        output_path=cover_image_path,
        grid=puzzles[0][1],
        highlights=solutions[0][2],
        highlight_color=tuple(int(cover_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)),  # convert hex to RGB
    )
    print(f"Cover image generated: {cover_image_path}")

    assemble_book_pdf(
        puzzles,
        solutions,
        pdf_output_path,
        puzzle_name,
        puzzle_count=len(puzzles),
        about_content=content_descriptions,
        grey_highlights=True,
        solution_scale=0.85,
        solution_left_margin_offset=30,
        solution_vertical_offset=40,
    )
    print(f"Book PDF generated: {pdf_output_path}")

    # Generate HTML description if requested
    if args.html_description:
        html_output_path = os.path.join(output_dir, f"{puzzle_name}-description.html")
        description = content_descriptions if content_descriptions else "Word Search Book"
        generate_html_description(html_output_path, puzzle_name, description, categories_data, catchphrase=data.get("catchphrase", ""))
