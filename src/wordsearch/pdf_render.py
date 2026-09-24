"""PDF rendering for wordsearch puzzles.
This module provides functionality to render word search puzzles
and their solutions to PDF format using the ReportLab library.
"""

import os
import math

from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from wordsearch import direction_to_delta, HighlightStyle

# Word-list font size range: the largest size in this range that still fits
# the puzzle's longest word within a table column is picked automatically,
# so short-word puzzles render bigger while long outlier words (e.g. Dutch
# compound words) never overflow past their column.
MAX_WORD_FONT_SIZE = 14
MIN_WORD_FONT_SIZE = 8


def _fit_word_font_size(words, available_width, font_name="Helvetica"):
    """
    Picks the largest font size (within MIN_WORD_FONT_SIZE..MAX_WORD_FONT_SIZE)
    at which every word in `words` fits within `available_width`.
    """
    if not words:
        return MAX_WORD_FONT_SIZE
    longest = max(words, key=len)
    for size in range(MAX_WORD_FONT_SIZE, MIN_WORD_FONT_SIZE - 1, -1):
        if stringWidth(longest, font_name, size) <= available_width:
            return size
    return MIN_WORD_FONT_SIZE


# pylint: disable=too-many-arguments,too-many-locals,too-many-statements,too-many-positional-arguments
def render_wordsearch_pdf(
    puzzle_output,
    title,
    grid,
    word_list,
    highlights=None,
    solution_output=None,
    highlight_style=HighlightStyle.RECT,
    page_num=None,
    grey_highlights=False,
    nav_index_target=None,
    nav_solution_target=None,
):
    """
    Render a wordsearch puzzle and its solution to a PDF file.

    Args:
        puzzle_output (str): File to save the PDF.
        title (str): Puzzle title.
        grid (list of list of str): The letter grid.
        word_list (list of str): List of words.
        highlights (list of dict): Optional. Each dict: {'word', 'start',
            'direction', 'length'}. If None, no solution is drawn.
        solution_output (str): Optional. File to save the solution PDF.
            If None, solution is added as a second page in the puzzle PDF.
        highlight_style (HighlightStyle): Style for highlighting solution words.
            HighlightStyle.RECT for rectangle outline, HighlightStyle.FILL for filled background.
        page_num (int): Optional. Page number to display at the bottom of the page.
        grey_highlights (bool): If True, use grey color for highlights instead of orange.
            Default is False (orange).
        nav_index_target (int): Optional. If set, draws a "← Index" label at
            the top-left of the puzzle page and reports its clickable rect
            in the returned dict (key "index") so the caller can add a real
            PDF link to that target page once the book is merged.
        nav_solution_target (int): Optional. Same as above but draws
            "Solution →" at the top-right, under key "solution".

    Returns:
        dict mapping "index"/"solution" (whichever targets were given) to
        (rect, target_page) tuples, rect = (x0, y0, x1, y1) in PDF points on
        this page. Empty dict when neither target was given.
    """

    # Ensure the output directory exists
    output_dir = os.path.dirname(puzzle_output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Create the PDF document
    styles = getSampleStyleSheet()
    small_title_style = ParagraphStyle(
        name="SmallTitle",
        parent=styles["Title"],
        fontSize=int(styles["Title"].fontSize * 0.8),
    )
    page_margin = 20  # Reduced margin for larger grid, 0.28 inch
    # cell_margin = 12  # 0.2 inch margin for table cells

    # --- Puzzle PDF ---
    # Only bottomMargin is tightened here: the letter grid itself is drawn
    # via a fixed-position canvas callback (draw_grid, below) anchored to
    # the top of the page independently of these doc margins, so shrinking
    # topMargin would push the word-list table up into the grid. Shrinking
    # bottomMargin instead frees vertical room for the table without moving
    # where it starts.
    doc = SimpleDocTemplate(
        puzzle_output,
        pagesize=A4,
        bottomMargin=page_margin,
    )
    elements = []
    # Title in uppercase and centered
    elements.append(Paragraph(title.upper(), styles["Title"]))
    elements.append(Spacer(1, 60))  # Increased space after title

    # Calculate grid size for spacer
    page_width, page_height = A4
    grid_size = len(grid)
    available_width = (page_width - 2 * page_margin) * 0.8
    available_height = (page_height - 2 * page_margin - 100) * 0.8
    cell_size = min(available_width, available_height) / grid_size
    grid_height = cell_size * grid_size
    # Add enough space for the grid and a little extra
    elements.append(Spacer(1, grid_height - 18))

    # Prepare word list in multiple columns, uppercase
    num_columns = 4
    words_upper = [w.upper() for w in word_list]
    words_upper.sort()
    rows = (len(words_upper) + num_columns - 1) // num_columns
    word_table_data = []
    for i in range(rows):
        row = []
        for j in range(num_columns):
            idx = i + j * rows
            if idx < len(words_upper):
                row.append(words_upper[idx])
            else:
                row.append("")
        word_table_data.append(row)
    # Set column widths to spread the table across the page
    col_width = (page_width - 4 * page_margin) / num_columns
    word_cell_padding = 6
    word_font_size = _fit_word_font_size(
        words_upper, col_width - 2 * word_cell_padding
    )
    word_table = Table(
        word_table_data, colWidths=[col_width] * num_columns, hAlign="CENTER"
    )
    word_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),  # Center text in each cell
                ("FONTSIZE", (0, 0), (-1, -1), word_font_size),
                ("LEFTPADDING", (0, 0), (-1, -1), word_cell_padding),
                ("RIGHTPADDING", (0, 0), (-1, -1), word_cell_padding),
            ]
        )
    )

    elements.append(word_table)

    nav_rects = {}

    # Custom grid drawing (fit to page, only outer border)
    def draw_grid(canvas, doc):  # pylint: disable=unused-argument
        page_width, page_height = A4
        grid_size = len(grid)
        available_width = (page_width - 2 * page_margin) * 0.8
        available_height = (page_height - 2 * page_margin) * 0.8
        cell_size = min(available_width, available_height) / grid_size
        grid_width = cell_size * grid_size
        grid_height = cell_size * grid_size
        grid_gap_y = 108  # delta from the top of the page to the grid
        start_x = (page_width - grid_width) / 2
        start_y = page_height - page_margin - grid_gap_y  # leave space for title

        # Draw outer border
        canvas.setLineWidth(2)
        canvas.rect(start_x, start_y - grid_height, grid_width, grid_height)

        # Draw letters (no cell borders)
        canvas.setFont("Helvetica-Bold", int(cell_size * 0.6))
        for r, row in enumerate(grid):
            for c, cell_letter in enumerate(row):
                x = start_x + c * cell_size + cell_size / 2
                # Adjusted y calculation to center letters properly
                y = start_y - r * cell_size - cell_size / 2 - cell_size * 0.2
                canvas.drawCentredString(x, y, cell_letter.upper())

        # Draw page number if provided
        canvas.setFont("Helvetica", 10)
        if page_num is not None:
            canvas.drawCentredString(
                page_width / 2, 0.5 * 72, str(page_num)
            )  # 0.5 inch from bottom

        canvas.drawString(0.5 * 72, 0.5 * 72, "Board Size: "+str(grid_size)+" | Words: "+str(len(words_upper)))

        # --- Navigation links (index / solution) ---
        # Drawn in the top margin, above where the title Paragraph starts
        # (SimpleDocTemplate's default topMargin, ~72pt, isn't touched -
        # see the comment on `doc` above). Only the visual label + its rect
        # are done here; the actual clickable PDF link annotation is added
        # afterwards by book_builder.assemble_book_pdf, once the final
        # merged document's page numbers are known.
        nav_font_size = 10
        nav_y = page_height - 40
        if nav_index_target is not None:
            label = "← Index"
            canvas.setFont("Helvetica", nav_font_size)
            canvas.setFillColorRGB(0, 0, 0.8)
            canvas.drawString(page_margin, nav_y, label)
            canvas.setFillColorRGB(0, 0, 0)
            label_width = canvas.stringWidth(label, "Helvetica", nav_font_size)
            nav_rects["index"] = (
                (page_margin - 4, nav_y - 4, page_margin + label_width + 4, nav_y + nav_font_size + 6),
                nav_index_target,
            )
        if nav_solution_target is not None:
            label = "Solution →"
            canvas.setFont("Helvetica", nav_font_size)
            canvas.setFillColorRGB(0, 0, 0.8)
            label_width = canvas.stringWidth(label, "Helvetica", nav_font_size)
            label_x = page_width - page_margin - label_width
            canvas.drawString(label_x, nav_y, label)
            canvas.setFillColorRGB(0, 0, 0)
            nav_rects["solution"] = (
                (label_x - 4, nav_y - 4, page_width - page_margin + 4, nav_y + nav_font_size + 6),
                nav_solution_target,
            )

    # --- Solution Page/PDF ---
    if highlights:
        elements_sol = []

        # Custom drawing for solution grid with highlights
        def draw_solution_grid(canvas, doc):  # pylint: disable=unused-argument
            page_width, page_height = A4
            page_margin = 36
            grid_size = len(grid)
            # Calculate available space and cell size
            available_width = (page_width - 2 * page_margin) * 0.45
            available_height = (page_height - 2 * page_margin - 100) * 0.45
            cell_size = min(available_width, available_height) / grid_size
            grid_width = cell_size * grid_size
            grid_height = cell_size * grid_size

            grid_gap_y = 96  # delta from the top of the page to the grid
            start_x = (page_width - grid_width) / 2
            start_y = page_height - page_margin - grid_gap_y  # Top of the grid

            # Draw only the outer border
            canvas.setLineWidth(1.5)
            canvas.rect(start_x, start_y - grid_height, grid_width, grid_height)

            # Draw letters (no cell borders)
            canvas.setFont("Helvetica-Bold", int(cell_size * 0.6))
            for r, row in enumerate(grid):
                for c, cell_letter in enumerate(row):
                    x = start_x + c * cell_size + cell_size / 2
                    y = (
                        start_y - r * cell_size - cell_size / 2 - cell_size * 0.2
                    )  # Adjust y for centering
                    canvas.drawCentredString(x, y, cell_letter.upper())

            # Draw highlights if provided
            if highlights:
                for h in highlights:
                    start_r, start_c = h["start"]
                    dr, dc = direction_to_delta(h["direction"])
                    length = h["length"]

                    if highlight_style == HighlightStyle.RECT:
                        rect_width_factor = 0.6

                        # Calculate the rectangle's start and end positions
                        end_r = start_r + dr * (length - 1)
                        end_c = start_c + dc * (length - 1)

                        # Find top-left corner (regardless of direction)
                        min_r = min(start_r, end_r)
                        min_c = min(start_c, end_c)

                        x = start_x + min_c * cell_size
                        y = start_y - min_r * cell_size

                        # Compute rectangle parameters
                        if dr == 0:  # Horizontal
                            rect_width = cell_size * length
                            rect_height = cell_size * rect_width_factor
                            angle = 0
                        elif dc == 0:  # Vertical
                            rect_width = cell_size * rect_width_factor
                            rect_height = cell_size * length
                            angle = 0
                        else:  # Diagonal
                            rect_width = (cell_size * length * 1.42) - (
                                cell_size * 0.4
                            )  # Approximate diagonal length
                            rect_height = cell_size * rect_width_factor
                            # Angle in degrees: atan2(dr, dc)
                            angle = math.degrees(math.atan2(dr, dc))

                        # Center of the rectangle (middle of the word)
                        mid_r = start_r + dr * (length - 1) / 2
                        mid_c = start_c + dc * (length - 1) / 2
                        center_x = start_x + (mid_c + 0.5) * cell_size
                        center_y = start_y - (mid_r + 0.5) * cell_size

                        # Draw rotated rounded rectangle
                        canvas.saveState()
                        canvas.translate(center_x, center_y)
                        canvas.rotate(
                            -angle
                        )  # Negative because PDF y-axis is inverted (0 at top)
                        if grey_highlights:
                            canvas.setStrokeColorRGB(0.5, 0.5, 0.5)  # Grey
                        else:
                            canvas.setStrokeColorRGB(1, 0.6, 0)  # Orange
                        canvas.setLineWidth(1.5)
                        radius = cell_size * 0.35
                        canvas.roundRect(
                            -rect_width / 2,
                            -rect_height / 2,
                            rect_width,
                            rect_height,
                            radius,
                            fill=0,
                            stroke=1,
                        )
                        canvas.restoreState()

                    elif highlight_style == HighlightStyle.FILL:
                        # Fill background of the word
                        for i in range(length):
                            rr = start_r + dr * i
                            cc = start_c + dc * i
                            lx = start_x + cc * cell_size
                            ly = start_y - (rr + 1) * cell_size
                            canvas.setFillColorRGB(
                                1, 1, 0, alpha=0.3
                            )  # Yellow highlight
                            canvas.rect(lx, ly, cell_size, cell_size, fill=1, stroke=0)

        if solution_output is None:
            # Add solution as a second page in the same PDF
            elements.append(PageBreak())
            elements.append(Paragraph(f"{title.upper()} - Solution", small_title_style))
            elements.append(Spacer(1, grid_height + 18))  # Space for the grid

            doc.build(elements, onFirstPage=draw_grid, onLaterPages=draw_solution_grid)
        else:
            # Create separate solution PDF
            doc.build(elements, onFirstPage=draw_grid)

            solution_dir = os.path.dirname(solution_output)
            if solution_dir:
                os.makedirs(solution_dir, exist_ok=True)
            doc_sol = SimpleDocTemplate(solution_output, pagesize=A4)
            elements_sol.append(
                Paragraph(f"{title.upper()} - Solution", small_title_style)
            )
            elements_sol.append(Spacer(1, grid_height + 18))  # Space for the grid

            doc_sol.build(
                elements_sol,
                onFirstPage=draw_solution_grid,
            )
    else:
        # No solution, just build the puzzle
        doc.build(elements, onFirstPage=draw_grid)

    return nav_rects


def draw_solution_grid_for_book(
    canvas, pos_x, pos_y, grid, highlights, cell_size, title, grey_highlights=False
):
    """
    Draws a solution grid with highlights for inclusion in a PDF book.
    Args:
        canvas: ReportLab canvas object.
        pos_x (float): X position to start drawing the grid.
        pos_y (float): Y position to start drawing the grid.
        grid (list of list of str): The letter grid.
        highlights (list of dict): Each dict: {'word', 'start', 'direction', 'length'}.
        cell_size (float): Size of each cell in the grid.
        title (str): Title of the puzzle.
        grey_highlights (bool): If True, use grey color for highlights instead of orange.
    """
    # Draw title
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawCentredString(
        pos_x + (len(grid) * cell_size) / 2,
        pos_y + len(grid) * cell_size + 14,
        title + " - Solution",
    )
    # Draw outer border
    canvas.setLineWidth(1.5)
    canvas.rect(pos_x, pos_y, len(grid) * cell_size, len(grid) * cell_size)
    # Draw letters
    canvas.setFont("Helvetica-Bold", int(cell_size * 0.6))
    for r, row in enumerate(grid):
        for c, cell_letter in enumerate(row):
            x = pos_x + c * cell_size + cell_size / 2
            y = (
                pos_y
                + (len(grid) - r - 1) * cell_size
                + cell_size / 2
                - cell_size * 0.2
            )
            canvas.drawCentredString(x, y, cell_letter.upper())
    # Draw highlights (rectangles)
    if highlights:
        for h in highlights:
            rect_width_factor = 0.6
            start_r, start_c = h["start"]
            dr, dc = direction_to_delta(h["direction"])
            length = h["length"]
            # Compute rectangle parameters (horizontal/vertical/diagonal)
            if dr == 0:  # Horizontal
                rect_width = cell_size * length
                rect_height = cell_size * rect_width_factor
                angle = 0
            elif dc == 0:  # Vertical
                rect_width = cell_size * rect_width_factor
                rect_height = cell_size * length
                angle = 0
            else:  # Diagonal
                rect_width = (cell_size * length * 1.42) - (
                    cell_size * (1 - rect_width_factor)
                )
                rect_height = cell_size * rect_width_factor

                angle = math.degrees(math.atan2(dr, dc))
            # Center of the rectangle (middle of the word)
            mid_r = start_r + dr * (length - 1) / 2
            mid_c = start_c + dc * (length - 1) / 2
            center_x = pos_x + (mid_c + 0.5) * cell_size
            center_y = pos_y + (len(grid) - (mid_r + 0.5)) * cell_size
            # Draw rotated rounded rectangle
            canvas.saveState()
            canvas.translate(center_x, center_y)
            canvas.rotate(-angle)
            if grey_highlights:
                canvas.setStrokeColorRGB(0.5, 0.5, 0.5)  # Grey
            else:
                canvas.setStrokeColorRGB(1, 0.6, 0)  # Orange
            canvas.setLineWidth(1.5)
            radius = cell_size * 0.35
            canvas.roundRect(
                -rect_width / 2,
                -rect_height / 2,
                rect_width,
                rect_height,
                radius,
                fill=0,
                stroke=1,
            )
            canvas.restoreState()


if __name__ == "__main__":
    # Example usage
    EXAMPLE_TITLE = "Sample Wordsearch: Colors"
    # fmt: off
    example_wordsearch_result = {
        "grid": [
            ["C", "R", "Y", "V", "C", "F", "U", "T", "S", "S", "B", "U"],
            ["C", "X", "P", "U", "M", "J", "Q", "I", "V", "L", "E", "F"],
            ["C", "J", "K", "C", "I", "B", "Y", "I", "U", "R", "Q", "Z"],
            ["W", "A", "R", "T", "X", "I", "O", "E", "F", "X", "C", "W"],
            ["Y", "W", "E", "I", "A", "L", "I", "G", "L", "A", "Y", "K"],
            ["X", "I", "G", "U", "E", "N", "O", "N", "I", "L", "W", "K"],
            ["W", "X", "V", "T", "P", "V", "P", "A", "B", "D", "O", "O"],
            ["M", "A", "Z", "U", "T", "K", "G", "R", "E", "E", "N", "W"],
            ["M", "I", "B", "Q", "K", "D", "C", "O", "E", "R", "L", "I"],
            ["A", "V", "H", "B", "S", "S", "V", "M", "X", "O", "W", "M"],
            ["L", "C", "M", "F", "K", "H", "Z", "O", "X", "M", "X", "P"],
            ["Q", "G", "A", "H", "M", "G", "B", "G", "S", "R", "Z", "E"],
        ],
        "words": ["ORANGE", "YELLOW", "INDIGO", "VIOLET", "GREEN", "BLUE"],
    }
    # fmt: on

    example_highlights = [
        {
            "word": "ORANGE",
            "start": (8, 7),
            "direction": "vertical_bottom_to_top",
            "length": 6,
        },
        {
            "word": "YELLOW",
            "start": (2, 6),
            "direction": "diagonal_top_left_to_bottom_right",
            "length": 6,
        },
        {
            "word": "INDIGO",
            "start": (8, 11),
            "direction": "diagonal_bottom_right_to_top_left",
            "length": 6,
        },
        {
            "word": "VIOLET",
            "start": (1, 8),
            "direction": "diagonal_top_right_to_bottom_left",
            "length": 6,
        },
        {
            "word": "GREEN",
            "start": (7, 6),
            "direction": "horizontal_left_to_right",
            "length": 5,
        },
        {
            "word": "BLUE",
            "start": (0, 10),
            "direction": "diagonal_top_right_to_bottom_left",
            "length": 4,
        },
        {
            "word": "RED",
            "start": (8, 9),
            "direction": "vertical_bottom_to_top",
            "length": 3,
        },
    ]

    example_puzzle_output = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "..", "out", "wordsearch_puzzle.pdf"
        )
    )
    example_solution_output = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "..", "out", "wordsearch_solution.pdf"
        )
    )
    example_combined_output = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "..", "out", "wordsearch_combined.pdf"
        )
    )

    # Example 1: Separate puzzle and solution PDFs
    render_wordsearch_pdf(
        puzzle_output=example_puzzle_output,
        title=EXAMPLE_TITLE,
        grid=example_wordsearch_result["grid"],
        word_list=example_wordsearch_result["words"],
        highlights=example_highlights,
        solution_output=example_solution_output,  # Solution in different file
        grey_highlights=False,
    )

    # Example 2: Combined puzzle and solution in one PDF
    render_wordsearch_pdf(
        puzzle_output=example_combined_output,
        title=EXAMPLE_TITLE,
        grid=example_wordsearch_result["grid"],
        word_list=example_wordsearch_result["words"],
        highlights=example_highlights,
        solution_output=None,  # Solution in same file
        grey_highlights=True,
    )
