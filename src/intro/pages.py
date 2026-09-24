"""
Functions for creating intro pages in word search books - Animals theme.
Adapted for 80 puzzles, large print, seniors target.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth

# How many index entries fit on one 2-column index page (see
# create_index_page): must stay in sync with that function's own layout math.
INDEX_ROWS_PER_COLUMN = 40
INDEX_ENTRIES_PER_PAGE = INDEX_ROWS_PER_COLUMN * 2


def create_blank_page(output_pdf):
    """Creates a blank page PDF."""
    page_width, page_height = letter
    c = canvas.Canvas(output_pdf, pagesize=letter)
    c.showPage()
    c.save()


def create_title_page(output_pdf, puzzle_name, puzzle_num=80, about_content=None):
    """
    Creates the title page.

    The "HOW TO SOLVE" and "ABOUT THIS BOOK" pages that used to follow are
    currently disabled (commented out below, not deleted) at the user's
    request - re-enable by uncommenting and moving the showPage()/save()
    calls back down.
    """
    page_width, page_height = letter
    c = canvas.Canvas(output_pdf, pagesize=letter)
    
    # Font sizes for large print (seniors-friendly)
    title_font_size = 36
    subtitle_font_size = 24
    body_font_size = 14
    small_font_size = 12
    
    # === PAGE 1: BLANK (already handled externally) ===
    
    # === PAGE 2: TITLE PAGE - DIVIDED INTO 2 LINES ===
    c.setFont("Helvetica-Bold", 32)  # Slightly reduced from 36pt
    
    # write the title form puzzle name variable uppercase, no underscores 
    clean_title = puzzle_name.replace("_", " ").upper()
    print(f"Creating title page for {clean_title} with {puzzle_num} puzzles.")
    c.drawCentredString(page_width / 2, page_height * 0.75, clean_title)
    c.drawCentredString(page_width / 2, page_height * 0.70, "WORD SEARCH")
    c.drawCentredString(page_width / 2, page_height * 0.58, "PUZZLES FOR ADULTS")

    c.setFont("Helvetica-Bold", subtitle_font_size)
    c.drawCentredString(page_width / 2, page_height * 0.48, f"{puzzle_num} Large-Print Themed Puzzles")

    c.setFont("Helvetica", small_font_size)
    c.drawCentredString(page_width / 2, page_height * 0.38, "Easy-to-Read • Perfect for Seniors")

    # Your author name
    author_name = "Puzzle Book Series"
    c.setFont("Helvetica", small_font_size)
    c.drawCentredString(page_width / 2, page_height * 0.1, author_name)
    
    c.showPage()
    c.save()

    # # === PAGE 3: INSTRUCTIONS + ABOUT - LEFT ALIGNED ===
    # # Instructions title
    # c.setFont("Helvetica-Bold", 20)
    # c.drawString(1.5*inch, page_height * 0.85, "HOW TO SOLVE")
    #
    # # Instructions list
    # c.setFont("Helvetica", body_font_size)
    # y_pos = page_height * 0.75
    # instructions = [
    #     "1. Read the themed word list below the puzzle",
    #     "2. Find where each word fits in the grid", 
    #     "3. Write letters in the squares using pen or pencil",
    #     "4. Check solutions at the back if needed"
    # ]
    #
    # for instr in instructions:
    #     c.drawString(1.5*inch, y_pos, instr)
    #     y_pos -= 0.4*inch
    #
    # # Large print note
    # y_pos -= 0.2*inch
    # c.setFont("Helvetica-Bold", body_font_size)
    # c.drawString(1.5*inch, y_pos, "Large print design for comfortable solving!")
    #
    # c.showPage()
    #
    # # === PAGE 4: ABOUT THIS BOOK (last before puzzles) ===
    # c.setFont("Helvetica-Bold", 20)
    # c.drawString(1.5*inch, page_height * 0.85, "ABOUT THIS BOOK")
    #
    # c.setFont("Helvetica", body_font_size)
    # y_pos = page_height * 0.75
    #
    # # About text
    # about_text = [
    #     "Discover 80 themed word search puzzles"
    # ]
    # # append additional about content if provided
    # if about_content:
    #     about_text = [
    #         f"Discover 80 themed word search puzzles featuring:",
    #     ]
    #     # Group about_content items in threes and append each group as a single string
    #     for i in range(0, len(about_content), 3):
    #         group = about_content[i:i+3]
    #         line = "  ".join(f"• {item}" for item in group)
    #         about_text.append(line)
    #
    #
    #
    # # continue about text
    # for line in about_text:
    #     c.drawString(1.5*inch, y_pos, line)
    #     y_pos -= 0.35*inch
    #
    # # Benefits
    # y_pos -= 0.2*inch
    # c.setFont("Helvetica-Bold", body_font_size)
    # c.drawString(1.5*inch, y_pos, "Perfect for:")
    # y_pos -= 0.3*inch
    #
    # benefits = [
    #     "• Brain training & relaxation",
    #     "• Seniors & adults", 
    #     "• Vocabulary building",
    #     "• Travel, gifts, or personal enjoyment"
    # ]
    #
    # c.setFont("Helvetica", body_font_size)
    # for benefit in benefits:
    #     c.drawString(1.5*inch, y_pos, benefit)
    #     y_pos -= 0.3*inch
    #
    # c.showPage()
    # c.save()
    #
    #
def create_intro_pages(merger, tmpdir, puzzle_name, puzzle_count, about_content=None):
    """
    Creates and appends the intro pages.

    The blank first page is currently disabled (commented out below, not
    deleted) at the user's request - probably wants a cover illustration
    there instead. Only the title page is appended; puzzle pages then
    start on page 2.
    """
    # # Blank page 1
    # blank_pdf = os.path.join(tmpdir, "blank.pdf")
    # create_blank_page(blank_pdf)
    # merger.append(blank_pdf)

    # Title page
    intro_pdf = os.path.join(tmpdir, "intro_complete.pdf")
    create_title_page(intro_pdf, puzzle_name, puzzle_count, about_content=about_content)
    merger.append(intro_pdf)


def create_index_page(output_pdf, entries, page_label=None):
    """
    Draws one 2-column index page.

    Args:
        output_pdf (str): file to save the PDF to.
        entries (list): list of (title, target_page) tuples to list on this
            page (already sliced to fit - see INDEX_ENTRIES_PER_PAGE).
            Filled column-major: column 1 top-to-bottom, then column 2.
        page_label: optional page number to print at the bottom.

    Returns:
        list of (rect, target_page) where rect = (x0, y0, x1, y1) in PDF
        points. The caller (book_builder.assemble_book_pdf) turns these into
        real clickable links once the whole book has been merged into one
        document and every page's final index is known - this function only
        draws pixels and reports back where it put each entry.
    """
    page_width, page_height = letter
    margin = 50
    gap = 30
    top = page_height - 100
    bottom = 50
    row_height = (top - bottom) / INDEX_ROWS_PER_COLUMN
    col_width = (page_width - 2 * margin - gap) / 2
    font_size = 11

    c = canvas.Canvas(output_pdf, pagesize=letter)

    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(page_width / 2, page_height - 70, "INDEX")

    rects = []
    for i, (title, target_page) in enumerate(entries):
        col = i // INDEX_ROWS_PER_COLUMN
        row = i % INDEX_ROWS_PER_COLUMN
        col_x = margin + col * (col_width + gap)
        row_top = top - row * row_height
        row_bottom = row_top - row_height
        text_y = row_bottom + row_height * 0.3

        page_str = str(target_page)
        page_str_width = stringWidth(page_str, "Helvetica", font_size)
        title_max_width = col_width - page_str_width - 15

        c.setFont("Helvetica", font_size)
        display_title = title
        while stringWidth(display_title, "Helvetica", font_size) > title_max_width and len(display_title) > 1:
            display_title = display_title[:-1]
        if display_title != title:
            display_title = display_title[:-1] + "…"

        c.drawString(col_x, text_y, display_title)
        c.drawRightString(col_x + col_width, text_y, page_str)

        rects.append(((col_x, row_bottom, col_x + col_width, row_top), target_page))

    if page_label is not None:
        c.setFont("Helvetica", 10)
        c.drawCentredString(page_width / 2, 0.5 * inch, str(page_label))

    c.showPage()
    c.save()
    return rects


def create_solution_intro_pages(output_pdf, title_text):
    """Creates a solution title page."""
    page_width, page_height = letter
    c = canvas.Canvas(output_pdf, pagesize=letter)
    
    # Font sizes
    title_font_size = 36
    
    # Title
    c.setFont("Helvetica-Bold", title_font_size)
    c.drawCentredString(page_width / 2, page_height / 2, title_text)
    
    c.showPage()
    c.save()