# RPG Rulebook PDF to Markdown Converter - Summary

## What Was Built

A Python script (`pdf_to_markdown.py`) that converts RPG rulebook PDF files into organized, well-formatted markdown files.

## Key Features

1. **Smart Text Extraction**: Uses pdfplumber with multiple extraction methods
2. **Structure Detection**: Automatically identifies headings and paragraphs
3. **Garbled Text Filtering**: Filters out corrupted text sections
4. **Batch Processing**: Process multiple PDFs at once
5. **Image OCR Support**: Optional OCR for image-based PDFs (requires PyTesseract)

## Files Created

- `pdf_to_markdown.py` - Main conversion script
- `README.md` - Usage documentation
- `requirements.txt` - Python dependencies
- `SUMMARY.md` - This file

## How to Use

### Basic Usage

```bash
# Install dependencies
pip install pdfplumber PyPDF2 python-dateutil

# Run the converter
python pdf_to_markdown.py
```

### Process Specific Files

```bash
python pdf_to_markdown.py path/to/file1.pdf path/to/file2.pdf
```

## Output Format

The script creates markdown files with proper structure:

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

## Technical Details

### Heading Detection

The script uses multiple patterns to identify headings:

1. Lines followed by empty lines and lowercase text
2. Lines significantly longer than surrounding text (main titles)
3. Lines ending with numbers (chapter/section numbers)
4. Roman numerals or numbered lists
5. All-caps lines of appropriate length
6. Short capitalized lines followed by paragraphs

### Text Cleaning

- Removes excessive whitespace
- Converts special characters to ASCII equivalents
- Filters out garbled text sections
- Preserves paragraph structure

## Limitations

1. **Image-based PDFs**: The provided example PDFs appear to be image-based with very limited text content. For best results with such PDFs, install PyTesseract for OCR support.

2. **Complex Layouts**: Some PDFs with complex layouts may require manual adjustment of heading detection parameters.

3. **Font Issues**: Some PDFs have font encoding issues that can result in garbled text extraction.

## Future Improvements

- Better handling of image-based PDFs with improved OCR
- More sophisticated layout analysis
- Table detection and formatting
- Automatic table of contents generation
- Support for additional output formats (HTML, EPUB)
