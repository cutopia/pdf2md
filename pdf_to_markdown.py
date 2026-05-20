#!/usr/bin/env python3
"""
RPG Rulebook PDF to Markdown Converter - Improved Version

This version uses model-based heading detection for more accurate results.
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

# Import our model-based heading detector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_heading_detector import ModelHeadingDetector, AdaptiveHeadingDetector


@dataclass
class PDFConfig:
    """Configuration for PDF processing"""
    output_dir: str = "markdown_output"
    max_pages: Optional[int] = None
    page_range: Optional[Tuple[int, int]] = None
    preserve_layout: bool = True
    extract_images: bool = False
    image_dir: str = "images"
    
    # Heading detection settings
    use_model_heading_detection: bool = True
    heading_confidence_threshold: float = 0.65
    
    # Formatting options
    heading_level_1: str = "#"
    heading_level_2: str = "##"
    heading_level_3: str = "###"


class PDFToMarkdownConverter:
    """Converts RPG rulebook PDF files to organized markdown files"""
    
    def __init__(self, config: Optional[PDFConfig] = None):
        self.config = config or PDFConfig()
        
        # Initialize heading detector
        if self.config.use_model_heading_detection:
            print("Initializing model-based heading detection...")
            self.heading_detector = AdaptiveHeadingDetector()
        else:
            print("Using rule-based heading detection (legacy mode)")
            from model_heading_detector import RuleBasedHeadingDetector
            self.heading_detector = RuleBasedHeadingDetector()
        
        self.stats = {
            "pages_processed": 0,
            "headings_found": 0,
            "tables_found": 0,
            "images_found": 0,
            "text_blocks": 0
        }
        
    def extract_text_with_structure(self, pdf_path: str) -> List[Dict]:
        """Extract text from PDF with structural information"""
        pages_content = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
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
                    
                    # Extract text
                    page_text = self._extract_page_text(page)
                    
                    if not page_text or len(page_text.strip()) < 10:
                        print(f"Warning: Insufficient text from page {page_num + 1}")
                        continue
                    
                    # Analyze structure using improved heading detection
                    content_structure = self._analyze_page_structure_improved(page_text, page_num)
                    
                    pages_content.append({
                        "page_number": page_num + 1,
                        "content": content_structure,
                        "width": float(page.width),
                        "height": float(page.height)
                    })
                    
                    self.stats["pages_processed"] += 1
                    
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {str(e)}")
            raise
            
        return pages_content
    
    def _extract_page_text(self, page) -> str:
        """Extract text from a pdfplumber page"""
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
        
        # Fallback extraction
        if not best_text or len(best_text.strip()) < 20:
            try:
                tables = page.extract_tables()
                table_text = ""
                for table in tables:
                    for row in table:
                        table_text += " ".join(cell for cell in row if cell) + "\n"
                
                simple_text = page.extract_text(x_tolerance=1, y_tolerance=1)
                
                if simple_text and len(simple_text.strip()) > 20:
                    best_text = simple_text
                elif table_text:
                    best_text = table_text
            except Exception:
                pass
        
        if best_text:
            best_text = self._clean_extracted_text(best_text)
        
        return best_text if best_text else ""
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean up corrupted text from PDF extraction"""
        # Fix common Unicode corruption patterns
        text = re.sub(r'\ue053', 'Th', text)
        text = re.sub(r'\x00', '', text)
        text = re.sub(r'[\u200b\u200c\u200d\uffff]', '', text)
        
        # Split long lines
        lines = text.split('\n')
        new_lines = []
        
        for line in lines:
            if len(line) > 200:
                sentences = re.split(r'(?<=[.!?])\s+', line)
                for sentence in sentences:
                    if len(sentence) > 50:
                        parts = re.split(r'\s+([A-Z][a-z]+)', sentence)
                        new_lines.extend(parts)
                    else:
                        new_lines.append(sentence)
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def _analyze_page_structure_improved(self, text: str, page_num: int) -> List[Dict]:
        """
        Analyze structure using improved heading detection
        
        This uses the model-based detector for more accurate results.
        """
        lines = text.split('\n')
        content_elements = []
        
        # Detect headings using our improved detector
        detected_headings = self.heading_detector.detect_headings(lines)
        
        current_section = {
            "type": "paragraph",
            "content": [],
            "level": 0,
            "title": ""
        }
        
        heading_indices = {h[0] for h in detected_headings}
        heading_info = {h[0]: (h[1], h[2]) for h in detected_headings}
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            if len(stripped_line) < 3:
                continue
            
            # Check if this line is a heading
            if i in heading_indices:
                # Save current section if it has content
                if current_section["content"]:
                    content_elements.append(current_section.copy())
                
                # Start new section with heading
                title, level = heading_info[i]
                current_section = {
                    "type": "heading",
                    "content": [],
                    "level": level,
                    "title": title
                }
            else:
                # Regular text content
                if not current_section["title"] and not current_section["content"]:
                    current_section["type"] = "paragraph"
                    current_section["content"].append(stripped_line)
                elif len(stripped_line) < 40 and stripped_line[0].isupper():
                    # Check if this might be a subheading
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                        if not next_line or (next_line and next_line[0].islower()):
                            current_section["content"].append(stripped_line)
                        else:
                            current_section["content"].append(stripped_line)
                    else:
                        current_section["content"].append(stripped_line)
                else:
                    if len(stripped_line) > 5:
                        current_section["content"].append(stripped_line)
        
        # Add final section
        if current_section["content"]:
            content_elements.append(current_section.copy())
        
        self.stats["text_blocks"] += len(content_elements)
        
        return content_elements
    
    def convert_to_markdown(self, pages_content: List[Dict], output_path: str) -> None:
        """Convert structured content to markdown format"""
        markdown_lines = []
        
        # Add header information
        markdown_lines.append(f"# RPG Rulebook - Converted from PDF")
        markdown_lines.append("")
        markdown_lines.append(f"*Converted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        markdown_lines.append("")
        
        current_chapter = ""
        consecutive_headings = 0
        
        for page in pages_content:
            content = page.get("content", [])
            
            for element in content:
                element_type = element.get("type", "paragraph")
                
                if element_type == "heading":
                    level = element.get("level", 1)
                    title = element.get("title", "")
                    
                    # Determine heading symbol
                    heading_symbol = self._get_heading_symbol(level)
                    
                    if level <= 2:
                        current_chapter = title
                    
                    markdown_lines.append(f"{heading_symbol} {title}")
                    self.stats["headings_found"] += 1
                    consecutive_headings += 1
                    
                elif element_type == "paragraph":
                    content_text = " ".join(element.get("content", []))
                    
                    if content_text:
                        # Clean up the text
                        content_text = self._clean_text(content_text)
                        
                        if content_text and not self._is_garbled_text(content_text):
                            # Add spacing before paragraphs after headings
                            if consecutive_headings > 0 and content_text:
                                markdown_lines.append("")
                            
                            markdown_lines.append(content_text)
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
        return symbols.get(level, "#" * level)
    
    def _clean_text(self, text: str) -> str:
        """Clean up extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common PDF issues
        text = re.sub(r'(?<!\s)-\n(?!\s)', '', text)  # Join hyphenated words
        text = re.sub(r'\n\s*\n', '\n\n', text)       # Normalize paragraph breaks
        
        return text.strip()
    
    def _is_garbled_text(self, text: str) -> bool:
        """Check if text appears to be garbled/corrupted"""
        # Check for excessive special characters
        special_char_count = len(re.findall(r'[=<>|_\-]{3,}', text))
        if special_char_count > 2:
            return True
        
        # Check for too many consecutive uppercase letters (likely corrupted)
        if re.search(r'[A-Z]{10,}', text):
            return True
        
        # Check ratio of special characters to letters
        alpha_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(re.sub(r'\s', '', text))
        
        if total_chars > 0 and alpha_chars / total_chars < 0.5:
            return True
        
        return False
    
    def process_pdf(self, pdf_path: str) -> Dict:
        """Process a single PDF file"""
        pages_content = self.extract_text_with_structure(pdf_path)
        
        # Generate output path
        input_path = Path(pdf_path)
        output_filename = f"{input_path.stem}.md"
        output_path = os.path.join(self.config.output_dir, output_filename)
        
        self.convert_to_markdown(pages_content, output_path)
        
        return {
            "input_file": pdf_path,
            "output_file": output_path,
            "stats": self.stats.copy()
        }
    
    def process_multiple_pdfs(self, pdf_paths: List[str]) -> List[Dict]:
        """Process multiple PDF files"""
        results = []
        
        for pdf_path in pdf_paths:
            result = self.process_pdf(pdf_path)
            results.append(result)
            
            # Reset stats for next file
            self.stats = {
                "pages_processed": 0,
                "headings_found": 0,
                "tables_found": 0,
                "images_found": 0,
                "text_blocks": 0
            }
        
        return results


def find_pdf_files(directory: str) -> List[str]:
    """Find all PDF files in a directory"""
    pdf_files = []
    
    for file in Path(directory).glob("*.pdf"):
        pdf_files.append(str(file))
    
    return sorted(pdf_files)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert RPG rulebook PDFs to Markdown")
    parser.add_argument("pdf_files", nargs="*", help="PDF files to process")
    parser.add_argument("--directory", "-d", default="sample_rpg_pdfs",
                       help="Directory containing PDF files (default: sample_rpg_pdfs)")
    parser.add_argument("--output", "-o", default="markdown_output",
                       help="Output directory (default: markdown_output)")
    parser.add_argument("--max-pages", "-m", type=int, default=None,
                       help="Maximum pages to process per file")
    parser.add_argument("--no-model", action="store_true",
                       help="Disable model-based heading detection (use legacy rules)")
    
    args = parser.parse_args()
    
    # Find PDF files
    pdf_files = args.pdf_files
    
    if not pdf_files:
        if os.path.exists(args.directory):
            pdf_files = find_pdf_files(args.directory)
            print(f"Found {len(pdf_files)} PDF files in {args.directory}")
        else:
            print(f"Error: Directory '{args.directory}' not found")
            sys.exit(1)
    
    if not pdf_files:
        print("No PDF files to process")
        sys.exit(0)
    
    # Create configuration
    config = PDFConfig()
    config.output_dir = args.output
    config.max_pages = args.max_pages
    config.use_model_heading_detection = not args.no_model
    
    # Create converter and process files
    converter = PDFToMarkdownConverter(config)
    
    print(f"\nProcessing {len(pdf_files)} file(s)...")
    results = converter.process_multiple_pdfs(pdf_files)
    
    # Print summary
    print("\n" + "="*50)
    print("PROCESSING SUMMARY")
    print("="*50)
    
    total_pages = sum(r["stats"]["pages_processed"] for r in results)
    total_headings = sum(r["stats"]["headings_found"] for r in results)
    
    print(f"Total pages processed: {total_pages}")
    print(f"Total headings found: {total_headings}")
    print(f"\nOutput files saved to: {args.output}/")
