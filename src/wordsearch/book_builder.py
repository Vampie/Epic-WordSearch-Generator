"""
Shared logic for assembling word search puzzle books.

This module factors out the puzzle-generation and PDF-assembly logic that
was previously duplicated between the `generate_ws_book` and
`generate_big_ws_book` scripts, so both can be implemented as thin
command-line wrappers around it.
"""

import os
import tempfile

from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PyPDF2.generic import AnnotationBuilder, RectangleObject
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from intro import (
    create_index_page,
    create_intro_pages,
    create_solution_intro_pages,
    INDEX_ENTRIES_PER_PAGE,
)
from wordsearch import generate
from wordsearch import pdf_render

_ORDINALS = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th", 7: "7th", 8: "8th"}


def find_json_in_data(filename, base_dir="data"):
    """
    Search for a JSON file named `filename` inside `base_dir` and its subfolders.

    - `filename` may be given with or without the `.json` extension.
    - Search is case-insensitive and returns the first exact filename match found.
    - Returns an absolute path if found, otherwise returns None.
    """
    if not filename:
        return None

    name = filename
    if name.lower().endswith(".json"):
        name = name[:-5]
    target_lower = (name + ".json").lower()

    if not os.path.isdir(base_dir):
        return None

    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.lower() == target_lower:
                return os.path.abspath(os.path.join(root, f))

    return None


def resolve_input_path(input_arg, base_dir="data"):
    """
    Resolves a CLI input argument to an actual file path: if `input_arg`
    already points to an existing file, it's returned as-is. Otherwise,
    `find_json_in_data` is used to look it up (with or without a folder
    prefix or `.json` extension) anywhere under `base_dir`. If nothing is
    found, `input_arg` is returned unchanged so the caller's own
    file-not-found handling kicks in.
    """
    if os.path.isfile(input_arg):
        return input_arg
    found = find_json_in_data(input_arg, base_dir=base_dir)
    return found if found else input_arg


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
    target_pages=None,
):
    """
    Draws up to 4 solution grids on a single page and saves as PDF.

    `scale`, `left_margin_offset` and `vertical_offset` allow callers to
    tune grid spacing/positioning (the "big book" layout uses a slightly
    smaller scale and extra offsets compared to the regular book layout).

    `target_pages`, if given, is a list of the same length as
    `solutions_chunk`: the page each solution's own puzzle lives on. Returns
    a list of (rect, target_page) - rect = (x0, y0, x1, y1) in PDF points -
    one per solution that had a target, for the caller to turn into a real
    clickable link once the book is merged (see assemble_book_pdf).
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
    link_rects = []
    for position, (sol_title, sol_grid, sol_highlights) in enumerate(solutions_chunk):
        grid_size = len(sol_grid)
        cell_size = grid_area / grid_size
        pos_x, pos_y = grid_positions[position]

        pdf_render.draw_solution_grid_for_book(
            c, pos_x, pos_y, sol_grid, sol_highlights, cell_size, sol_title,
            grey_highlights=grey_highlights,
        )

        if target_pages is not None and position < len(target_pages):
            grid_top = pos_y + grid_size * cell_size
            rect = (pos_x, pos_y, pos_x + grid_size * cell_size, grid_top + 26)
            link_rects.append((rect, target_pages[position]))

    if page_num is not None:
        draw_page_number(c, page_num)

    c.showPage()
    c.save()
    return link_rects


def _add_link_annotations(pdf_path, link_annotations):
    """
    Re-opens `pdf_path` and adds a clickable link for each
    (source_page, rect, target_page) in `link_annotations` (all 1-indexed
    page numbers; rect = (x0, y0, x1, y1) in that page's own PDF points),
    then overwrites the file. Split out from assemble_book_pdf because links
    can only be added once every page has a final, permanent page number -
    i.e. after the whole book has been merged into one document.
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.append(reader)

    num_pages = len(writer.pages)
    for source_page, rect, target_page in link_annotations:
        if not 1 <= source_page <= num_pages or not 1 <= target_page <= num_pages:
            continue
        annotation = AnnotationBuilder.link(
            rect=RectangleObject(rect),
            target_page_index=target_page - 1,
        )
        writer.add_annotation(page_number=source_page - 1, annotation=annotation)

    with open(pdf_path, "wb") as f:
        writer.write(f)


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
    add_navigation=True,
):
    """
    Assembles intro pages, one puzzle per page, and grouped solution pages
    into a single merged PDF book at `output_pdf`.

    When `add_navigation` is True (default), a 2-column index (one or more
    pages, right after the title page) is added, and clickable links are
    wired up: each index entry jumps to its puzzle, each puzzle page links
    back to the index (top-left) and forward to its solution (top-right),
    and each solution grid links back to its puzzle.

    This book's layout is fully deterministic (title, then index, then one
    page per puzzle, then a solutions title page, then solutions 4-per-page
    in the same order as `puzzles`), so every page number is computed up
    front before anything is drawn - that's what makes the cross-references
    possible without a second rendering pass.
    """
    num_puzzles = len(puzzles)

    num_index_pages = 0
    if add_navigation and num_puzzles:
        num_index_pages = -(-num_puzzles // INDEX_ENTRIES_PER_PAGE)  # ceil div

    first_puzzle_page = 2 + num_index_pages
    puzzle_pages = [first_puzzle_page + i for i in range(num_puzzles)]
    solutions_title_page = first_puzzle_page + num_puzzles
    first_solution_page = solutions_title_page + 1
    solution_pages = [first_solution_page + i // 4 for i in range(num_puzzles)]

    index_target_page = 2 if num_index_pages else None

    with tempfile.TemporaryDirectory() as tmpdir:
        merger = PdfMerger()
        link_annotations = []  # (source_page, rect, target_page), 1-indexed

        # --- Title page ---
        create_intro_pages(
            merger, tmpdir, puzzle_name, puzzle_count if puzzle_count is not None else num_puzzles,
            about_content=about_content,
        )

        # --- Index pages ---
        if num_index_pages:
            index_entries = [(puzzles[i][0], puzzle_pages[i]) for i in range(num_puzzles)]
            for page_i in range(num_index_pages):
                chunk = index_entries[page_i * INDEX_ENTRIES_PER_PAGE:(page_i + 1) * INDEX_ENTRIES_PER_PAGE]
                index_page_num = 2 + page_i
                index_pdf = os.path.join(tmpdir, f"index_{page_i}.pdf")
                rects = create_index_page(index_pdf, chunk, page_label=index_page_num)
                merger.append(index_pdf)
                for rect, target in rects:
                    link_annotations.append((index_page_num, rect, target))

        # --- Puzzles: one per page ---
        for idx, (title, grid, words) in enumerate(puzzles):
            puzzle_pdf = os.path.join(tmpdir, f"puzzle_{idx}.pdf")
            page_number = puzzle_pages[idx]
            nav_rects = pdf_render.render_wordsearch_pdf(
                puzzle_output=puzzle_pdf,
                title=title,
                grid=grid,
                word_list=words,
                highlights=None,
                solution_output=None,
                page_num=page_number,
                grey_highlights=grey_highlights,
                nav_index_target=index_target_page,
                nav_solution_target=solution_pages[idx] if add_navigation else None,
            )
            merger.append(puzzle_pdf)
            for rect, target in nav_rects.values():
                link_annotations.append((page_number, rect, target))

        # --- Solutions title page ---
        solutions_title_pdf = os.path.join(tmpdir, "solutions_title.pdf")
        create_solution_intro_pages(solutions_title_pdf, "Solutions")
        merger.append(solutions_title_pdf)

        # --- Solutions: 4 per page ---
        for i in range(0, len(solutions), 4):
            chunk = solutions[i:i + 4]
            chunk_targets = puzzle_pages[i:i + 4] if add_navigation else None
            solution_pdf = os.path.join(tmpdir, f"solution_{i // 4}.pdf")
            page_number = solution_pages[i]
            rects = create_solution_page(
                chunk,
                solution_pdf,
                page_num=page_number,
                grey_highlights=grey_highlights,
                scale=solution_scale,
                left_margin_offset=solution_left_margin_offset,
                vertical_offset=solution_vertical_offset,
                target_pages=chunk_targets,
            )
            merger.append(solution_pdf)
            for rect, target in rects:
                link_annotations.append((page_number, rect, target))

        # Write the merged PDF
        merger.write(output_pdf)
        merger.close()

    if link_annotations:
        _add_link_annotations(output_pdf, link_annotations)
