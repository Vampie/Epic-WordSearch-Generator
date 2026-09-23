"""
Shared logic for assembling word search puzzle books.

This module factors out the puzzle-generation and PDF-assembly logic that
was previously duplicated between the `generate_ws_book` and
`generate_big_ws_book` scripts, so both can be implemented as thin
command-line wrappers around it.
"""

import os
import tempfile

from PyPDF2 import PdfMerger
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from intro import create_intro_pages, create_solution_intro_pages
from wordsearch import generate
from wordsearch import pdf_render

_ORDINALS = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th", 7: "7th", 8: "8th"}


def output_filename(base_name, doc_type, ext, suffix=None):
    """
    Builds a standardized "<base_name>_<doc_type>[_<suffix>].<ext>" filename,
    e.g. "animals_book.pdf" or "animals_book_2.pdf".
    """
    stem = f"{base_name}_{doc_type}"
    if suffix is not None:
        stem = f"{stem}_{suffix}"
    return f"{stem}.{ext}"


def reserve_output_suffix(output_dir, base_name, outputs):
    """
    Finds the smallest suffix (None for no suffix, then 1, 2, 3, ...) such
    that none of the "<base_name>_<doc_type>[_<suffix>].<ext>" files for
    (doc_type, ext) in `outputs` already exist in output_dir.

    This lets a set of related exports produced in one run (e.g. a book PDF,
    its cover image, and its data JSON) share one consistent suffix instead
    of silently overwriting a previous run's files or drifting out of sync
    with each other.
    """
    suffix = None
    while True:
        if not any(
            os.path.exists(os.path.join(output_dir, output_filename(base_name, doc_type, ext, suffix)))
            for doc_type, ext in outputs
        ):
            return suffix
        suffix = 1 if suffix is None else suffix + 1


def clear_output_variants(output_dir, base_name, outputs):
    """
    Removes any existing "<base_name>_<doc_type>[_<suffix>].<ext>" files for
    the given (doc_type, ext) pairs, including numbered "_1", "_2", ...
    variants, so a fresh, unsuffixed "final" file can be written without
    leftover older versions lying around. Returns the list of removed paths.
    """
    if not os.path.isdir(output_dir):
        return []
    removed = []
    suffix = None
    while True:
        found_any = False
        for doc_type, ext in outputs:
            path = os.path.join(output_dir, output_filename(base_name, doc_type, ext, suffix))
            if os.path.exists(path):
                os.remove(path)
                removed.append(path)
                found_any = True
        if suffix is None:
            suffix = 1
            continue
        if not found_any:
            break
        suffix += 1
    return removed


def resolve_output_suffix(output_dir, base_name, outputs, force=False):
    """
    Decides what suffix this run's outputs should use.

    If `force` is True, any existing unsuffixed or numbered ("_1", "_2", ...)
    variants of `outputs` are deleted first, and this run writes the plain
    "<base_name>_<doc_type>.<ext>" files (suffix None) as the new "final"
    version. Otherwise, behaves like `reserve_output_suffix`: finds a free
    suffix so nothing existing gets overwritten.
    """
    if force:
        clear_output_variants(output_dir, base_name, outputs)
        return None
    return reserve_output_suffix(output_dir, base_name, outputs)


def generate_single_puzzle(title, words, size, use_basic=False, verbose=False, max_attempts=1):
    """
    Generate one puzzle, retrying up to `max_attempts` times if some words
    fail to place. Returns the generated puzzle (or None on total failure),
    and prints a warning if words remained unplaced after all attempts.
    """
    puzzle = None
    for attempt in range(max_attempts):
        puzzle = generate.generate_puzzle(
            title, words, grid_size=size, use_basic=use_basic, verbose=verbose
        )
        if not puzzle.failed_words:
            if attempt > 0:
                ordinal = _ORDINALS.get(attempt + 1, f"{attempt + 1}th")
                print(f"Puzzle '{title}' generated at the {ordinal} attempt")
            break

    if puzzle is not None and puzzle.failed_words:
        print(
            f"Warning: Could not place the following words in puzzle "
            f"'{title}': {puzzle.failed_words}"
        )

    return puzzle


def draw_page_number(c, page_num):
    """Draws a page number at the bottom center of a PDF page."""
    page_width, _ = letter
    c.setFont("Helvetica", 10)
    c.drawCentredString(page_width / 2, 0.5 * 72, str(page_num))  # 0.5 inch from bottom


def create_solution_page(
    solutions_chunk,
    output_pdf,
    page_num=None,
    grey_highlights=False,
    scale=1.0,
    left_margin_offset=0,
    vertical_offset=0,
):
    """
    Draws up to 4 solution grids on a single page and saves as PDF.

    `scale`, `left_margin_offset` and `vertical_offset` allow callers to
    tune grid spacing/positioning (the "big book" layout uses a slightly
    smaller scale and extra offsets compared to the regular book layout).
    """
    page_width, page_height = letter
    margin = 36
    grid_area = ((page_width - 2 * margin) / 2) * scale
    grid_positions = [
        # Top-left
        (margin + left_margin_offset, page_height / 2 + margin / 2 + vertical_offset),
        # Top-right
        (page_width / 2 + margin / 2, page_height / 2 + margin / 2 + vertical_offset),
        # Bottom-left
        (margin + left_margin_offset, margin + 50 + vertical_offset),
        # Bottom-right
        (page_width / 2 + margin / 2, margin + 50 + vertical_offset),
    ]

    c = canvas.Canvas(output_pdf, pagesize=letter)
    for position, (sol_title, sol_grid, sol_highlights) in enumerate(solutions_chunk):
        grid_size = len(sol_grid)
        cell_size = grid_area / grid_size
        pos_x, pos_y = grid_positions[position]

        pdf_render.draw_solution_grid_for_book(
            c, pos_x, pos_y, sol_grid, sol_highlights, cell_size, sol_title,
            grey_highlights=grey_highlights,
        )

    if page_num is not None:
        draw_page_number(c, page_num)

    c.showPage()
    c.save()


def assemble_book_pdf(
    puzzles,
    solutions,
    output_pdf,
    puzzle_name,
    puzzle_count=None,
    about_content=None,
    grey_highlights=False,
    solution_scale=1.0,
    solution_left_margin_offset=0,
    solution_vertical_offset=0,
):
    """
    Assembles intro pages, one puzzle per page, and grouped solution pages
    into a single merged PDF book at `output_pdf`.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        merger = PdfMerger()

        # --- Create intro pages ---
        create_intro_pages(
            merger, tmpdir, puzzle_name, puzzle_count if puzzle_count is not None else len(puzzles),
            about_content=about_content,
        )

        # Track current page number (intro has 4 pages)
        current_page = 5

        # --- Puzzles: one per page ---
        for idx, (title, grid, words) in enumerate(puzzles):
            puzzle_pdf = os.path.join(tmpdir, f"puzzle_{idx}.pdf")
            pdf_render.render_wordsearch_pdf(
                puzzle_output=puzzle_pdf,
                title=title,
                grid=grid,
                word_list=words,
                highlights=None,
                solution_output=None,
                page_num=current_page,
                grey_highlights=grey_highlights,
            )
            merger.append(puzzle_pdf)
            current_page += 1

        # --- Solutions title page ---
        solutions_title_pdf = os.path.join(tmpdir, "solutions_title.pdf")
        create_solution_intro_pages(solutions_title_pdf, "Solutions")
        merger.append(solutions_title_pdf)
        current_page += 1

        # --- Solutions: 4 per page ---
        for i in range(0, len(solutions), 4):
            chunk = solutions[i:i + 4]
            solution_pdf = os.path.join(tmpdir, f"solution_{i // 4}.pdf")
            create_solution_page(
                chunk,
                solution_pdf,
                page_num=current_page,
                grey_highlights=grey_highlights,
                scale=solution_scale,
                left_margin_offset=solution_left_margin_offset,
                vertical_offset=solution_vertical_offset,
            )
            merger.append(solution_pdf)
            current_page += 1

        # Write the merged PDF
        merger.write(output_pdf)
        merger.close()
