# RPG Rulebook PDF to Markdown Converter

A Python script that converts RPG rulebook PDF files into organized, well-formatted markdown files. It handles both text-based and image-based PDFs with optional OCR support.

## Features

- **Smart Text Extraction**: Uses pdfplumber for accurate text extraction from complex PDF layouts
- **Structure Detection**: Automatically identifies headings, paragraphs, and document structure
- **Multiple Format Support**: Handles various PDF structures common in RPG rulebooks
- **Clean Markdown Output**: Produces well-formatted markdown with proper heading hierarchy
- **Batch Processing**: Process multiple PDF files at once
- **Image OCR Support**: Optional OCR for image-based PDFs using PyTesseract

## Requirements

### Basic Installation

```bash
pip install pdfplumber PyPDF2 python-dateutil
```

### Optional (for OCR support on image-based PDFs)

```bash
# Install tesseract OCR system package first:
# Ubuntu/Debian: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

pip install pytesseract Pillow
```

## Usage

### Basic Usage

```bash
python pdf_to_markdown.py
```

This will automatically find and process all PDF files in the `sample_rpg_pdfs` directory.

### Process Specific Files

```bash
python pdf_to_markdown.py path/to/file1.pdf path/to/file2.pdf
```

### Custom Output Directory

```bash
python pdf_to_markdown.py --output my_output_dir file1.pdf file2.pdf
```

## Output Structure

The script creates markdown files with the following structure:

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

## Configuration

The script can be customized through the `PDFConfig` class:

```python
config = PDFConfig()
config.output_dir = "markdown_output"
config.max_pages = 50  # Process only first 50 pages
config.page_range = (1, 20)  # Process pages 1-20
config.preserve_layout = True
```

## Example Output

The converted markdown files maintain the original document structure with:

- **Level 1 Headings** (`#`): Main chapter titles
- **Level 2 Headings** (`##`): Major sections
- **Level 3 Headings** (`###`): Subsections
- **Paragraphs**: Regular text content

## Advanced Usage

### Programmatic Usage

```python
from pdf_to_markdown import PDFToMarkdownConverter, PDFConfig

# Create configuration
config = PDFConfig()
config.output_dir = "custom_output"

# Create converter
converter = PDFToMarkdownConverter(config)

# Process a single file
result = converter.process_pdf("rulebook.pdf")

# Process multiple files
results = converter.process_multiple_pdfs([
    "file1.pdf",
    "file2.pdf", 
    "file3.pdf"
])
```

## Troubleshooting

### No Text Extracted

Some PDFs may have complex layouts or be image-based. The script will automatically try OCR if available:

```bash
# Install OCR support for better results with image-based PDFs
pip install pytesseract Pillow
sudo apt-get install tesseract-ocr  # Ubuntu/Debian
```

### Poor Heading Detection

Adjust the heading detection patterns in `_detect_heading_pattern()` method to better match your specific PDF structure.

## License

This script is provided as-is for personal and educational use.
