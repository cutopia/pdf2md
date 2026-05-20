#!/usr/bin/env python3
"""
Heading Analysis Tool

This tool analyzes text to determine which lines are likely headings.
It can use either rule-based or model-based approaches.
"""

import sys
import re
from pathlib import Path

# Import our heading detectors
sys.path.insert(0, str(Path(__file__).parent))
from model_heading_detector import (
    ModelHeadingDetector, 
    RuleBasedHeadingDetector,
    AdaptiveHeadingDetector
)


def analyze_text_for_headings(text: str, use_model: bool = True):
    """Analyze text and identify headings"""
    
    lines = text.split('\n')
    
    if use_model:
        detector = ModelHeadingDetector()
        detector.initialize()
        headings = detector.detect_headings(lines)
        
        print(f"Model-based detection found {len(headings)} potential headings:")
        for idx, line, confidence in headings[:10]:  # Show first 10
            print(f"  Line {idx}: '{line[:60]}...' (confidence: {confidence:.2f})")
            
    else:
        detector = RuleBasedHeadingDetector()
        headings = detector.detect_headings(lines)
        
        print(f"Rule-based detection found {len(headings)} potential headings:")
        for idx, line, level in headings[:10]:  # Show first 10
            print(f"  Line {idx}: '{line[:60]}...' (level: {level})")
    
    return headings


def analyze_pdf_file(pdf_path: str, use_model: bool = True):
    """Analyze a PDF file for headings"""
    try:
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            # Try text extraction first
            page = pdf.pages[0]
            text = page.extract_text()
            
            if not text or len(text.strip()) < 10:
                print("No text found, trying OCR...")
                
                # Try OCR
                try:
                    im = page.to_image(resolution=150)
                    img = im.original.convert('L')
                    
                    import pytesseract
                    text = pytesseract.image_to_string(img)
                    
                    if not text or len(text.strip()) < 10:
                        print("OCR also failed to extract sufficient text")
                        return []
                        
                except ImportError:
                    print("OCR not available (pytesseract)")
                    return []
            
            # Analyze the extracted text
            headings = analyze_text_for_headings(text, use_model)
            return headings
            
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        return []


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze text/PDF for headings")
    parser.add_argument("input", help="Input text file or PDF file")
    parser.add_argument("--no-model", action="store_true",
                       help="Use rule-based detection instead of model")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: File '{args.input}' not found")
        sys.exit(1)
    
    if input_path.suffix.lower() == '.pdf':
        headings = analyze_pdf_file(str(input_path), not args.no_model)
    else:
        # Text file
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        headings = analyze_text_for_headings(text, not args.no_model)
    
    print(f"\nTotal: {len(headings)} potential headings detected")


if __name__ == "__main__":
    main()
