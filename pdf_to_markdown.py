#!/usr/bin/env python3
"""
RPG Rulebook PDF to Markdown Converter

This script converts RPG rulebook PDF files into organized, well-formatted markdown files.
It handles various PDF structures and creates a clean, readable markdown output.

Requirements:
    pip install pdfplumber PyPDF2 python-dateutil
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber is required. Install with: pip install pdfplumber")
    sys.exit(1)

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Warning: PyPDF2 not installed. Some features may be limited.")


@dataclass
class PDFConfig:
    """Configuration for PDF processing"""
    output_dir: str = "markdown_output"
    max_pages: Optional[int] = None  # None means process all pages
    page_range: Optional[Tuple[int, int]] = None  # (start_page, end_page) - 0-indexed
    preserve_layout: bool = True
    extract_images: bool = False
    image_dir: str = "images"
    
    # Formatting options
    heading_level_1: str = "#"
    heading_level_2: str = "##"
    heading_level_3: str = "###"
    bold_pattern: str = r"\*\*(.*?)\*\*"
    italic_pattern: str = r"\*(.*?)\*"
    
    # Table formatting
    table_format: str = "markdown"  # markdown, grid, or pipe


class PDFToMarkdownConverter:
    """Converts RPG rulebook PDF files to organized markdown files"""
    
    def __init__(self, config: Optional[PDFConfig] = None):
        self.config = config or PDFConfig()
        self.stats = {
            "pages_processed": 0,
            "headings_found": 0,
            "tables_found": 0,
            "images_found": 0,
            "text_blocks": 0
        }
        
    def extract_text_with_structure(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from PDF with structural information (headings, paragraphs, etc.)
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing page content with structure info
        """
        pages_content = []
        
        try:
            # Try using pdfplumber for better text extraction
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                # Determine page range to process
                start_page = 0
                end_page = total_pages
                
                if self.config.page_range:
                    start_page, end_page = self.config.page_range
                    end_page = min(end_page, total_pages)
                elif self.config.max_pages:
                    end_page = min(self.config.max_pages, total_pages)
                
                print(f"Processing {pdf_path} ({start_page + 1}-{end_page} of {total_pages} pages)")
                
                for page_num in range(start_page, end_page):
                    page = pdf.pages[page_num]
                    
                    # Extract text with better settings
                    page_text = self._extract_page_text(page)
                    
                    if not page_text or len(page_text.strip()) < 10:
                        print(f"Warning: Insufficient text extracted from page {page_num + 1}, trying image-based extraction...")
                        
                        # Try to extract text from images on the page
                        image_text = self._extract_text_from_images(page)
                        if image_text and len(image_text.strip()) > 20:
                            page_text = image_text
                            print(f"  Successfully extracted {len(image_text)} chars from images")
                        else:
                            print(f"Warning: No text extracted from page {page_num + 1} (text or images)")
                            continue
                    
                    # Analyze structure
                    content_structure = self._analyze_page_structure(page_text, page_num)
                    
                    pages_content.append({
                        "page_number": page_num + 1,
                        "content": content_structure,
                        "width": float(page.width),
                        "height": float(page.height)
                    })
                    
                    self.stats["pages_processed"] += 1
                    
                    # Progress indicator every 25 pages
                    if (page_num - start_page + 1) % 25 == 0:
                        print(f"  Processed {page_num - start_page + 1} pages...")
                    
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {str(e)}")
            raise
            
        return pages_content
    
    def _extract_page_text(self, page) -> str:
        """
        Extract text from a pdfplumber page with improved settings
        
        Args:
            page: pdfplumber page object
            
        Returns:
            Extracted text string
        """
        # Try multiple extraction methods and combine results
        methods = [
            {"x_tolerance": 3, "y_tolerance": 3, "layout": False},
            {"x_tolerance": 5, "y_tolerance": 5, "layout": False},
            {"x_tolerance": 2, "y_tolerance": 2, "layout": True}
        ]
        
        best_text = ""
        max_length = 0
        
        for method in methods:
            try:
                text = page.extract_text(**method)
                if text and len(text) > max_length:
                    max_length = len(text)
                    best_text = text
            except Exception:
                continue
        
        # If still no good text, try with minimal tolerance
        if not best_text or len(best_text.strip()) < 20:
            try:
                # Try extracting tables and combining with text
                tables = page.extract_tables()
                table_text = ""
                for table in tables:
                    for row in table:
                        table_text += " ".join(cell for cell in row if cell) + "\n"
                
                # Try simple extraction as fallback
                simple_text = page.extract_text(x_tolerance=1, y_tolerance=1)
                
                if simple_text and len(simple_text.strip()) > 20:
                    best_text = simple_text
                elif table_text:
                    best_text = table_text
            except Exception:
                pass
        
        # If still no text, try PyPDF2 as fallback
        if not best_text or len(best_text.strip()) < 10:
            try:
                from PyPDF2 import PdfReader
                
                # Get the page number in the overall document
                pdfplumber_pdf = page.parent
                page_num = None
                for i, p in enumerate(pdfplumber_pdf.pages):
                    if p == page:
                        page_num = i
                        break
                
                if page_num is not None:
                    with open(pdfplumber_pdf.path, 'rb') as f:
                        reader = PdfReader(f)
                        if page_num < len(reader.pages):
                            pypdf_text = reader.pages[page_num].extract_text()
                            if pypdf_text and len(pypdf_text.strip()) > 10:
                                best_text = pypdf_text
            except Exception:
                pass
        
        return best_text if best_text else ""
    
    def _extract_text_from_images(self, page) -> str:
        """
        Extract text from images on a PDF page using OCR
        
        Args:
            page: pdfplumber page object
            
        Returns:
            Extracted text string
        """
        try:
            # Get the page as an image using pdfplumber's built-in method
            im = page.to_image(resolution=150)  # 150 DPI should be good for OCR
            
            if not hasattr(im, 'original') or im.original is None:
                return ""
            
            # Try to use pytesseract if available
            try:
                import pytesseract
                
                # Convert to grayscale and enhance
                img = im.original.convert('L')
                
                # Apply thresholding to preprocess the image
                # img = img.point(lambda x: 0 if x < 128 else 255, '1')
                
                # Perform OCR
                text = pytesseract.image_to_string(img)
                return text
                
            except ImportError:
                print("  PyTesseract not available for OCR")
                return ""
                
        except Exception as e:
            print(f"  Image extraction error: {e}")
            return ""
    
    def _analyze_page_structure(self, text: str, page_num: int) -> List[Dict]:
        """
        Analyze the structure of extracted text to identify headings, paragraphs, etc.
        
        Args:
            text: Extracted text from a PDF page
            page_num: Page number (0-indexed)
            
        Returns:
            List of structured content elements
        """
        lines = text.split('\n')
        content_elements = []
        
        current_section = {
            "type": "paragraph",
            "content": [],
            "level": 0,
            "title": ""
        }
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Skip very short lines that are likely page numbers or artifacts
            if len(stripped_line) < 3:
                continue
            
            # Check for garbled text and skip it
            if self._is_garbled_text(stripped_line):
                continue
            
            # Check for heading patterns (common in RPG rulebooks)
            heading_match = self._detect_heading_pattern(stripped_line, lines, i)
            
            if heading_match:
                # Save current section if it has content
                if current_section["content"]:
                    content_elements.append(current_section.copy())
                
                # Start new section with heading
                level, title = heading_match
                current_section = {
                    "type": "heading",
                    "content": [],
                    "level": level,
                    "title": title
                }
            else:
                # Regular text content - check if this is a continuation or new paragraph
                if not current_section["title"] and not current_section["content"]:
                    # First line of a new section - likely a heading if it's short and capitalized
                    if self._is_likely_heading(stripped_line, lines, i):
                        current_section = {
                            "type": "heading",
                            "content": [],
                            "level": 1,
                            "title": stripped_line
                        }
                    else:
                        current_section["type"] = "paragraph"
                        current_section["content"].append(stripped_line)
                elif len(stripped_line) < 50 and stripped_line[0].isupper():
                    # Short line that might be a subheading
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                        if not next_line or (next_line and next_line[0].islower()):
                            # Save current section
                            if current_section["content"]:
                                content_elements.append(current_section.copy())
                            
                            # Start new heading section
                            current_section = {
                                "type": "heading",
                                "content": [],
                                "level": 3,
                                "title": stripped_line
                            }
                        else:
                            current_section["content"].append(stripped_line)
                    else:
                        current_section["content"].append(stripped_line)
                else:
                    # Only add if it's not a single character or very short garbled text
                    if len(stripped_line) > 5:  # Skip very short lines
                        current_section["content"].append(stripped_line)
        
        # Add final section if it has content
        if current_section["content"]:
            content_elements.append(current_section.copy())
        
        self.stats["text_blocks"] += len(content_elements)
        
        return content_elements
    
    def _detect_heading_pattern(self, line: str, all_lines: List[str], line_index: int) -> Optional[Tuple[int, str]]:
        """
        Detect if a line is likely a heading and determine its level
        
        Args:
            line: The line to check
            all_lines: All lines in the document
            line_index: Index of current line
            
        Returns:
            Tuple of (heading_level, heading_text) or None
        """
        # Skip very short lines or lines that look like page numbers
        if len(line) < 5 or re.match(r'^\d+$', line):
            return None
        
        # Pattern 1: Lines followed by empty lines and then lowercase text (typical heading pattern)
        if line_index + 2 < len(all_lines):
            next_line = all_lines[line_index + 1].strip()
            following_line = all_lines[line_index + 2].strip() if line_index + 2 < len(all_lines) else ""
            
            # If current line is followed by empty line and then lowercase text, it's likely a heading
            if not next_line and following_line and following_line[0].islower():
                return (2, line)
        
        # Pattern 2: Lines that are significantly longer than surrounding lines (likely main titles)
        if line_index > 1 and line_index < len(all_lines) - 2:
            prev_lines = [all_lines[line_index - i].strip() for i in range(1, 3) if line_index - i >= 0]
            next_lines = [all_lines[line_index + i].strip() for i in range(1, 3) if line_index + i < len(all_lines)]
            
            all_neighbors = prev_lines + next_lines
            if all_neighbors:
                avg_neighbor_len = sum(len(n) for n in all_neighbors) / len(all_neighbors)
                
                # If current line is much longer than neighbors, it might be a main heading
                if len(line) > avg_neighbor_len * 1.5 and len(line) > 20:
                    return (1, line)
        
        # Pattern 3: Lines ending with numbers (chapter/section numbers)
        number_pattern = re.match(r'^(.+?)(\d+[\.\s]*.*)$', line)
        if number_pattern:
            return (2, line)
        
        # Pattern 4: Lines starting with Roman numerals or numbers
        roman_numeral = re.match(r'^([IVXLCDM]+\.?\s+.+)', line, re.IGNORECASE)
        arabic_number = re.match(r'^(\d+\.\s+.+)', line)
        
        if roman_numeral:
            return (2, roman_numeral.group(1))
        if arabic_number:
            return (3, arabic_number.group(1))
        
        # Pattern 5: Lines with all caps and significant length (but not too long)
        if line.isupper() and len(line) > 10 and len(line) < 80:
            return (2, line.title())
        
        # Pattern 6: Short lines that might be section headings
        if 5 < len(line) < 40 and not any(char in line for char in ['.', '?', '!']):
            # Check if next line is empty or starts with lowercase (indicating paragraph)
            if line_index + 1 < len(all_lines):
                next_line = all_lines[line_index + 1].strip()
                if not next_line or (next_line and next_line[0].islower()):
                    return (3, line)
        
        # Pattern 7: Lines that look like chapter titles (short, capitalized words)
        if re.match(r'^([A-Z][a-z]+\.?\s+){1,4}$', line):
            return (2, line)
        
        return None
    
    def _is_likely_heading(self, line: str, all_lines: List[str], line_index: int) -> bool:
        """Check if a line is likely a heading"""
        # Check line length
        if len(line) < 5 or len(line) > 100:
            return False
        
        # Check if it's followed by an empty line or paragraph
        if line_index + 1 < len(all_lines):
            next_line = all_lines[line_index + 1].strip()
            if not next_line or (next_line and next_line[0].islower()):
                return True
        
        # Check for common heading characteristics
        if line[0].isupper() and line[-1] not in ['.', ':', '?', '!']:
            return True
            
        return False
    
    def convert_to_markdown(self, pages_content: List[Dict], output_path: str) -> None:
        """
        Convert structured content to markdown format
        
        Args:
            pages_content: List of page content dictionaries
            output_path: Path for the output markdown file
        """
        markdown_lines = []
        
        # Add header information
        markdown_lines.append(f"# RPG Rulebook - Converted from PDF")
        markdown_lines.append("")
        markdown_lines.append(f"*Converted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        markdown_lines.append("")
        
        current_chapter = ""
        consecutive_headings = 0
        
        for page in pages_content:
            # Add page separator (only between pages, not at the beginning)
            if self.stats["pages_processed"] > 1 and len(markdown_lines) > 5:
                markdown_lines.append(f"---\n*Page {page['page_number']}*\n---")
            
            content = page.get("content", [])
            
            for element in content:
                element_type = element.get("type", "paragraph")
                
                if element_type == "heading":
                    level = element.get("level", 1)
                    title = element.get("title", "")
                    
                    # Determine heading symbol
                    heading_symbol = self._get_heading_symbol(level)
                    
                    # Add chapter tracking
                    if level <= 2:
                        current_chapter = title
                    
                    markdown_lines.append(f"{heading_symbol} {title}")
                    self.stats["headings_found"] += 1
                    consecutive_headings += 1
                    
                elif element_type == "paragraph":
                    content_text = " ".join(element.get("content", []))
                    
                    # Clean up the text
                    content_text = self._clean_text(content_text)
                    
                    if content_text:
                        # Skip garbled text - check each line individually
                        lines_to_keep = []
                        for line in content_text.split('\n'):
                            line = line.strip()
                            if line and not self._is_garbled_text(line):
                                lines_to_keep.append(line)
                        
                        # Only add paragraph if it has non-garbled content
                        if lines_to_keep:
                            filtered_content = '\n'.join(lines_to_keep)
                            
                            # Add spacing before paragraphs after headings
                            if consecutive_headings > 0 and filtered_content:
                                markdown_lines.append("")
                            
                            markdown_lines.append(filtered_content)
                            consecutive_headings = 0
        
        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_lines))
        
        print(f"Markdown file saved to: {output_path}")
    
    def _get_heading_symbol(self, level: int) -> str:
        """Get the appropriate heading symbol for a given level"""
        symbols = {
            1: self.config.heading_level_1,
            2: self.config.heading_level_2,
            3: self.config.heading_level_3,
            4: "####",
            5: "#####",
            6: "######"
        }
        return symbols.get(level, "#")
    
    def _clean_text(self, text: str) -> str:
        """Clean and format text for markdown output"""
        # Remove excessive whitespace but preserve paragraph breaks
        text = re.sub(r' +', ' ', text)
        
        # Clean up common PDF artifacts
        text = text.replace('•', '-').replace('·', '-')
        text = text.replace('\u2013', '-').replace('\u2014', '--')  # em-dash and en-dash
        text = text.replace('\u2018', "'").replace('\u2019', "'")  # smart quotes
        text = text.replace('\u201C', '"').replace('\u201D', '"')  # smart quotes
        
        # Remove trailing whitespace from lines
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        
        return '\n'.join(cleaned_lines).strip()
    
    def _is_garbled_text(self, text: str) -> bool:
        """
        Check if text appears to be garbled or corrupted
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears garbled
        """
        # Skip very short text
        if len(text) < 30:
            return False
        
        # Check for excessive single characters separated by spaces (common in garbled text)
        words = text.split()
        if len(words) < 10:
            return False
        
        # Count single character "words"
        single_chars = sum(1 for word in words if len(word) == 1 and word.isalpha())
        
        # If more than 15% of words are single characters, likely garbled
        if single_chars / len(words) > 0.15:
            return True
        
        # Check for unusual character patterns (common in garbled text)
        if re.search(r'\b[a-zA-Z]\s+[a-zA-Z]\s+[a-zA-Z]\s+', text):
            return True
        
        # Check for very high ratio of punctuation to words
        punctuation_count = len(re.findall(r'[•·\u2013\u2014]', text))
        if len(words) > 15 and punctuation_count / len(words) > 0.4:
            return True
        
        # Check for mixed case patterns that look like encoding issues
        if re.search(r'\b[A-Z][a-z]{1,2}\s+[A-Z][a-z]{1,2}\s+[A-Z][a-z]{1,2}', text):
            return True
        
        # Check for very long lines with unusual spacing (common in garbled text)
        if len(text) > 500 and re.search(r'\b[a-zA-Z]\s+[a-zA-Z]\s+[a-zA-Z]', text):
            return True
        
        # Check for extremely high ratio of spaces to characters
        space_count = text.count(' ')
        char_count = len([c for c in text if c.isalpha()])
        if char_count > 0 and space_count / char_count > 1.5:
            return True
        
        # Check for very long lines with unusual spacing (common in garbled text)
        if len(text) > 400:
            # Split into words and check for patterns
            word_list = text.split()
            if len(word_list) > 20:
                # Count consecutive single-letter words
                consecutive_single = 0
                max_consecutive = 0
                for word in word_list:
                    if len(word) == 1 and word.isalpha():
                        consecutive_single += 1
                        max_consecutive = max(max_consecutive, consecutive_single)
                    else:
                        consecutive_single = 0
                
                # If more than 5 consecutive single-letter words, likely garbled
                if max_consecutive > 5:
                    return True
        
        return False
    
    def process_pdf(self, pdf_path: str, output_path: Optional[str] = None) -> Dict:
        """
        Process a single PDF file and convert to markdown
        
        Args:
            pdf_path: Path to the input PDF
            output_path: Optional path for output markdown (defaults to same name as PDF)
            
        Returns:
            Dictionary with processing statistics
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Generate output path if not provided
        if not output_path:
            pdf_name = Path(pdf_path).stem
            output_path = os.path.join(self.config.output_dir, f"{pdf_name}.md")
        
        print(f"\nProcessing: {pdf_path}")
        
        # Extract content with structure
        pages_content = self.extract_text_with_structure(pdf_path)
        
        if not pages_content:
            raise ValueError("No content extracted from PDF")
        
        # Convert to markdown
        self.convert_to_markdown(pages_content, output_path)
        
        return {
            "input_file": pdf_path,
            "output_file": output_path,
            "statistics": self.stats.copy()
        }
    
    def process_multiple_pdfs(self, pdf_paths: List[str], 
                             output_dir: Optional[str] = None) -> List[Dict]:
        """
        Process multiple PDF files
        
        Args:
            pdf_paths: List of paths to PDF files
            output_dir: Optional directory for outputs
            
        Returns:
            List of processing results
        """
        if output_dir:
            self.config.output_dir = output_dir
        
        results = []
        
        for pdf_path in pdf_paths:
            try:
                result = self.process_pdf(pdf_path)
                results.append(result)
                
                # Reset stats for next file (except totals)
                self.stats["pages_processed"] = 0
                self.stats["text_blocks"] = 0
                
            except Exception as e:
                print(f"Error processing {pdf_path}: {str(e)}")
                results.append({
                    "input_file": pdf_path,
                    "error": str(e),
                    "success": False
                })
        
        return results


def create_sample_config() -> PDFConfig:
    """Create a sample configuration for testing"""
    config = PDFConfig()
    config.output_dir = "rpg_markdown_output"
    config.preserve_layout = True
    return config


def main():
    """Main entry point for the script"""
    
    # Default paths
    default_pdf_dir = "sample_rpg_pdfs"
    output_directory = "markdown_output"
    
    print("=" * 60)
    print("RPG Rulebook PDF to Markdown Converter")
    print("=" * 60)
    
    # Check if sample directory exists and has PDFs
    pdf_files = []
    
    if os.path.exists(default_pdf_dir):
        for file in os.listdir(default_pdf_dir):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(default_pdf_dir, file))
    
    if not pdf_files:
        print(f"\nNo PDF files found in {default_pdf_dir}")
        print("Please provide PDF file paths as arguments or place PDFs in the sample_rpg_pdfs directory.")
        
        # Show usage
        print("\nUsage:")
        print("  python pdf_to_markdown.py <pdf_file1> [pdf_file2] ...")
        print("  python pdf_to_markdown.py --all [output_directory]")
        sys.exit(0)
    
    print(f"\nFound {len(pdf_files)} PDF file(s):")
    for i, pdf in enumerate(pdf_files, 1):
        size = os.path.getsize(pdf) / (1024 * 1024)  # Size in MB
        print(f"  {i}. {os.path.basename(pdf)} ({size:.1f} MB)")
    
    # Create converter with configuration
    config = create_sample_config()
    converter = PDFToMarkdownConverter(config)
    
    # Process the PDFs
    print("\nStarting conversion...")
    results = converter.process_multiple_pdfs(pdf_files, output_directory)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Conversion Summary")
    print("=" * 60)
    
    total_pages = sum(r.get("statistics", {}).get("pages_processed", 0) for r in results)
    total_headings = sum(r.get("statistics", {}).get("headings_found", 0) for r in results)
    total_blocks = sum(r.get("statistics", {}).get("text_blocks", 0) for r in results)
    
    print(f"Total pages processed: {total_pages}")
    print(f"Headings found: {total_headings}")
    print(f"Text blocks extracted: {total_blocks}")
    
    print("\nOutput files:")
    for result in results:
        if "output_file" in result:
            output_size = os.path.getsize(result["output_file"]) / 1024  # Size in KB
            print(f"  - {result['output_file']} ({output_size:.1f} KB)")
    
    print("\nConversion complete!")
    
    return results


if __name__ == "__main__":
    main()
