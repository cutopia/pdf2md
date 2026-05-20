# RPG Rulebook PDF to Markdown Converter - Complete Solution

## Overview

This solution provides a robust Python script for converting RPG rulebook PDF files into organized, well-formatted markdown files. It handles various PDF structures and includes features for text cleaning, structure detection, and optional OCR support.

## Files Created

1. **pdf_to_markdown.py** - Main conversion script (500+ lines)
2. **README.md** - Comprehensive usage documentation
3. **requirements.txt** - Python dependencies
4. **SUMMARY.md** - Technical summary
5. **SOLUTION.md** - This file

## Key Features

### 1. Smart Text Extraction
- Uses pdfplumber with multiple extraction methods
- Falls back to PyPDF2 when needed
- Handles various PDF encodings and layouts

### 2. Structure Detection
- Automatically identifies headings at multiple levels
- Distinguishes between main titles, sections, and subsections
- Preserves document hierarchy in output

### 3. Text Cleaning & Filtering
- Removes excessive whitespace
- Converts special characters to ASCII equivalents
- Filters out garbled/corrupted text sections
- Cleans up common PDF artifacts

### 4. Batch Processing
- Process multiple PDF files at once
- Progress indicators during conversion
- Comprehensive statistics and summaries

## Usage Examples

### Basic Conversion

```bash
# Install dependencies
pip install pdfplumber PyPDF2 python-dateutil

# Run with default settings (processes sample_rpg_pdfs directory)
python pdf_to_markdown.py
```

### Process Specific Files

```bash
python pdf_to_markdown.py path/to/file1.pdf path/to/file2.pdf
```

### Custom Output Directory

```bash
python pdf_to_markdown.py --output my_output_dir file1.pdf file2.pdf
```

## Output Format

The script creates well-structured markdown files:

```markdown
# RPG Rulebook - Converted from PDF

*Converted on: 2024-05-19*

---

*Page 1*
---

# Main Chapter Title

Content of the chapter...

## Subsection

More content...
```

## Heading Detection Patterns

The script uses multiple patterns to identify headings:

1. **Empty line followed by lowercase text** - Typical heading pattern
2. **Significantly longer than neighbors** - Likely main title
3. **Ending with numbers** - Chapter/section indicators
4. **Roman numerals or numbered lists** - Structured headings
5. **All-caps lines** - Section headers (appropriately sized)
6. **Short capitalized lines** - Subsections

## Technical Implementation

### Core Classes

- `PDFConfig` - Configuration for PDF processing
- `PDFToMarkdownConverter` - Main conversion logic

### Key Methods

- `extract_text_with_structure()` - Extracts text with structural info
- `_detect_heading_pattern()` - Identifies heading patterns
- `_analyze_page_structure()` - Analyzes page layout
- `convert_to_markdown()` - Generates markdown output
- `_is_garbled_text()` - Filters corrupted text

## Dependencies

### Required
```bash
pip install pdfplumber PyPDF2 python-dateutil
```

### Optional (for OCR support)
```bash
# Install tesseract OCR system package first:
sudo apt-get install tesseract-ocr  # Ubuntu/Debian
brew install tesseract             # macOS

pip install pytesseract Pillow
```

## Troubleshooting

### No Text Extracted

Some PDFs may have complex layouts or be image-based. The script will automatically try multiple extraction methods.

For image-based PDFs, install OCR support:

```bash
pip install pytesseract Pillow
sudo apt-get install tesseract-ocr  # Ubuntu/Debian
```

### Poor Heading Detection

Adjust the heading detection patterns in `_detect_heading_pattern()` method to better match your specific PDF structure.

## Example Output

The converted markdown files maintain the original document structure with:

- **Level 1 Headings** (`#`): Main chapter titles
- **Level 2 Headings** (`##`): Major sections  
- **Level 3 Headings** (`###`): Subsections
- **Paragraphs**: Regular text content

## Limitations

1. **Image-based PDFs**: The provided example PDFs contain images with limited text content. For best results, install PyTesseract for OCR support.

2. **Complex Layouts**: Some PDFs with complex layouts may require manual adjustment of heading detection parameters.

3. **Font Issues**: Some PDFs have font encoding issues that can result in garbled text extraction.

## Future Improvements

- Better handling of image-based PDFs with improved OCR
- More sophisticated layout analysis
- Table detection and formatting
- Automatic table of contents generation
- Support for additional output formats (HTML, EPUB)
