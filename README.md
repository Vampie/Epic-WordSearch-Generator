# 🚆📚 Fantastic Train - Wordsearch Generator

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

[//]: # (Add your CI badge below if available)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/runarion/fantastic-train-wordsearch-generator/actions) <!-- Replace with real CI badge if available -->

A Python library for generating professional Word Search puzzles and puzzle books. Perfect for creating educational materials, activity books, or recreational puzzle collections.

---

## 📑 Table of Contents

- [🚆📚 Fantastic Train - Wordsearch Generator](#-fantastic-train---wordsearch-generator)
  - [📑 Table of Contents](#-table-of-contents)
  - [✨ Features](#-features)
    - [Planned Features:](#planned-features)
  - [🚀 Installation](#-installation)
    - [From Source](#from-source)
  - [⚡ Quick Start](#-quick-start)
    - [Requirements](#requirements)
  - [📖 Usage](#-usage)
    - [1. Generate Single Page Puzzles](#1-generate-single-page-puzzles)
    - [2. Generate Complete Puzzle Books](#2-generate-complete-puzzle-books)
    - [3. Generate Large Puzzle Books with Variations](#3-generate-large-puzzle-books-with-variations)
    - [Validation](#validation)
  - [🏗️ Project Structure](#️-project-structure)
  - [🧪 Running Tests](#-running-tests)
  - [📋 Roadmap](#-roadmap)
  - [🤝 Contributing](#-contributing)
  - [📄 License](#-license)
  - [👤 Author](#-author)
  - [🙏 Acknowledgments](#-acknowledgments)
  - [📚 Example Output](#-example-output)
    - [📸 Screenshots / Previews](#-screenshots--previews)

---

A Python library for generating professional Word Search puzzles and puzzle books. Perfect for creating educational materials, activity books, or recreational puzzle collections.

## ✨ Features

- [x] 🎯 **Customizable Grid Sizes** - Generate puzzles from small (8x8) to large (30x30) grids
- [x] 📝 **Flexible Word Lists** - Import words from JSON files or provide them programmatically
- [x] 📚 **Batch Generation** - Create multiple puzzles for complete puzzle books
- [x] 🖨️ **Export Formats** - Output puzzles to PDF and DOCX formats
- [x] 📖 **Complete Book Generation** - Generate full PDF books with cover pages, intro pages, and solutions
- [x] 🎲 **Randomization** - Generate unique puzzles from the same word list
- [x] 📦 **Pre-made Collections** - Includes ready-to-use word lists (Animals, Travel, Food, Jobs)

### Planned Features:

- [ ] 🎨 **Multiple Difficulty Levels** - Control word placement directions (8-directional or basic 3-directional)
- [ ] 🌟 **Future Formats** - PNG/SVG export (planned)
- [ ] ✅ **Solution Keys** - Automatically generate answer keys with highlighted words

## 🚀 Installation

### From Source

Clone the repository:

```bash
git clone https://github.com/runarion/fantastic-train-wordsearch-generator.git
cd fantastic-train-wordsearch-generator
```

Install the package with dependencies:

```bash
pip install -e .
```

---

## ⚡ Quick Start

Generate a sample puzzle page as PDF:

```bash
python -m scripts.generate_ws_page data/input_page.json output/
```

Find your generated PDF in the `output/` folder.

---

### Requirements

- Python 3.8 or higher
- Dependencies:
  - `python-docx>=1.2.0` - DOCX export
  - `reportlab>=4.4.5` - PDF generation
  - `PyPDF2>=3.0.1` - PDF manipulation
- Development dependencies (optional):
  - `pytest>=9.0.0` - Testing
  - `pylint>=4.0.0` - Code linting
  - `black>=25.0.0` - Code formatting
  - `isort>=7.0.0` - Import sorting
  - `flake8>=7.3.0` - Style checking

Install with development dependencies:

```bash
pip install -e ".[dev]"
```

## 📖 Usage

The project includes three main scripts for different use cases:

### 1. Generate Single Page Puzzles

Generate individual puzzle pages with solutions.

```bash
python -m scripts.generate_ws_page data/input_page.json output/
```

**Options:**

- `input` - Input file, json format (required). Can also be a bare name
  (with or without `.json`) looked up under `data/`.
- `output` - Output folder (required)
- `-b, --basic` - Use basic directions only (horizontal left-to-right, vertical top-to-bottom, diagonal top-left to bottom-right)
- `--docx` - Also generate DOCX output (a PDF is always generated)
- `-f, --force` - Overwrite the final output files instead of adding a `_1`/`_2`/... suffix

**Input JSON Format:**

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

Sample file: [`data/input_page.json`](data/input_page.json)
  
Output: PDF and/or DOCX files will be saved in the specified `output/` folder.

### 2. Generate Complete Puzzle Books

Generate a complete PDF book with title page, puzzles, and solutions section.

```bash
python -m scripts.generate_ws_book data/input_book.json output/
```

**Options:**

- `input` - Input file, json format (required). Can also be a bare name
  (with or without `.json`) looked up under `data/`.
- `output` - Output folder (required)
- `-n, --name` - Name of the output book (without extension)
- `-f, --force` - Overwrite the final `<name>_book.pdf` instead of adding a `_1`/`_2`/... suffix

**Input Format:** Same as single page, with a book `title` at the root level.

Sample file: [`data/input_book.json`](data/input_book.json)
  
Output: The generated book will be saved as `output/<name>_book.pdf`.

### 3. Generate Large Puzzle Books with Variations

Generate a large puzzle book with multiple variations of each puzzle theme.

```bash
python -m scripts.generate_big_ws_book data/books/01_animals_20_lists.json output/
```

**Options:**

- `input` - Input file, json format (required). Can also be a bare name
  (with or without `.json`) looked up under `data/` and its subfolders.
- `output` - Output folder (required)
- `-n, --name` - Name of the output book (without extension)
- `-c, --copies` - Number of copies per puzzle (default: 4)
- `-t, --input-type` - Type of input file: 'wordlist' for puzzle definitions (generates new puzzles), 'puzzles' for previously generated puzzle data (reuses puzzles)
- `-w, --words` - Default number of words per puzzle when not set per-puzzle via `count` (default: 20)
- `-d, --html-description` - Generate an HTML file with the title and description of the book (default: False)
- `--cover` - Also generate a cover image (off by default)
- `--save-data` - Also save the generated puzzles/solutions to a `_data.json` file for later reuse with `-t puzzles` (off by default)
- `-f, --force` - Overwrite the final book/cover/data/description files instead of adding a `_1`/`_2`/... suffix

**Input Format:**

Sample files with 20 puzzles each in the folder [`data/books/`](data/books/).
  
Output: The large book will be saved as `output/<name>_bigbook.pdf`. Pass `--cover`/`--save-data` to also get a cover image and data JSON.

### Validation

Validate your JSON puzzle files before generation:

```bash
python -m scripts.validate_books data/books/
```

**Options:**

- `input_path` - Path to either a JSON file or a folder containing JSON files

---

## 🏗️ Project Structure

```txt
fantastic-train-wordsearch-generator/
├── data/                       # Input data files
│   ├── input_page.json        # Sample single page input
│   ├── input_book.json        # Sample book input
│   └── books/                 # Pre-made puzzle collections
├── scripts/                   # Executable scripts
│   ├── generate_ws_page.py   # Single page generator
│   ├── generate_ws_book.py   # Book generator
│   ├── generate_big_ws_book.py # Large book with variations
│   └── validate_books.py     # JSON validation tool
├── src/                       # Source code
│   ├── wordsearch/           # Core puzzle generation
│   │   ├── generate.py       # Puzzle generation algorithm
│   │   ├── pdf_render.py     # PDF rendering
│   │   ├── docx_export.py    # DOCX export
│   │   └── cover_image.py    # Cover page generation
│   └── intro/                # Book intro pages
│       └── pages.py          # Intro page templates
├── tests/                     # Unit tests
│   ├── test_basic.py
│   ├── test_generate.py
│   └── test_pdf_render.py
├── docs/                      # Documentation
├── releases/                  # Generated release files
├── pyproject.toml            # Project configuration
├── LICENSE                   # Apache 2.0 license
└── README.md                 # This file
```

## 🧪 Running Tests

Run all tests:

```bash
pytest tests/
```

Test results will be shown in the terminal. For more details, see the [tests/](tests/) folder.

Run specific test files:

```bash
pytest tests/test_generate.py
pytest tests/test_pdf_render.py
```

Run tests with verbose output:

```bash
pytest tests/ -v
```

## 📋 Roadmap

- [x] PDF generation with customizable styling
- [x] DOCX export functionality
- [x] Complete book generation with cover pages
- [x] Multiple puzzle variations from same word list
- [x] Pre-made word list collections (Animals, Travel, Food, Jobs)
- [x] Solution highlighting in PDF/DOCX
- [ ] PNG/SVG export functionality
- [ ] Theme support (colors, fonts, borders)
- [ ] Multi-language support
- [ ] Web API interface
- [ ] GUI application
- [ ] Interactive puzzle solving mode

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Runarion**

- GitHub: [@runarion](https://github.com/runarion)

## 🙏 Acknowledgments

- Inspired by classic word search puzzle books
- Built with Python and ReportLab for professional PDF generation
- Special thanks to all contributors

---

## 📚 Example Output

The generator creates professional-quality puzzle books with:

- Custom cover pages with title and imagery
- Introduction pages explaining puzzle rules
- One puzzle per page with word lists
- Dedicated solutions section with highlighted answers
- Page numbering throughout
- Consistent formatting and styling

### 📸 Screenshots / Previews

<!-- Add screenshots or sample output images here -->
<!-- Example: -->
<!-- ![Sample Puzzle Page](docs/sample_puzzle_page.png) -->

---

Made with ❤️ for puzzle enthusiasts everywhere!
