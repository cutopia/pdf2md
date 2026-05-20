#!/usr/bin/env python3
"""Test script to debug PDF text extraction with more methods"""

import pdfplumber
from PyPDF2 import PdfReader

# Test with one of our PDFs
pdf_path = "sample_rpg_pdfs/Those_Dark_Places.pdf"

print(f"Testing PDF: {pdf_path}")

# Try with pdfplumber - get all characters
with pdfplumber.open(pdf_path) as pdf:
    print(f"\n=== PdfPlumber Analysis ===")
    print(f"Total pages: {len(pdf.pages)}")
    
    for page_num in range(min(3, len(pdf.pages))):
        page = pdf.pages[page_num]
        
        # Get all characters
        chars = page.chars
        print(f"\nPage {page_num + 1}: {len(chars)} characters")
        
        if chars:
            # Show unique fonts
            fonts = set(c.get('fontname', 'unknown') for c in chars)
            print(f"Fonts found: {fonts}")
            
            # Show some sample text
            sample_text = ''.join(c['text'] for c in chars[:100])
            print(f"Sample text (first 100 chars): {repr(sample_text)}")
        
        # Try with very low tolerance
        try:
            text_low_tol = page.extract_text(x_tolerance=0, y_tolerance=0)
            if text_low_tol:
                print(f"With x/y_tolerance=0: {len(text_low_tol)} chars")
                print("First 300 chars:", repr(text_low_tol[:300]))
        except Exception as e:
            print(f"Error with low tolerance: {e}")

# Try with PyPDF2
print("\n=== PyPDF2 Analysis ===")
try:
    reader = PdfReader(pdf_path)
    print(f"Pages in PyPDF2: {len(reader.pages)}")
    
    for page_num in range(min(3, len(reader.pages))):
        page = reader.pages[page_num]
        text = page.extract_text()
        if text:
            print(f"\nPage {page_num + 1}: {len(text)} chars")
            print("First 300 chars:", repr(text[:300]))
        else:
            print(f"Page {page_num + 1}: No text extracted")
except Exception as e:
    print(f"PyPDF2 error: {e}")

# Try with pdfminer
try:
    from pdfminer.high_level import extract_text
    
    print("\n=== PDFMiner Analysis ===")
    text = extract_text(pdf_path, maxpages=3)
    if text:
        print(f"PDFMiner extracted: {len(text)} chars")
        print("First 500 chars:", repr(text[:500]))
    else:
        print("PDFMiner: No text extracted")
except ImportError:
    print("\nPDFMiner not installed")
except Exception as e:
    print(f"\nPDFMiner error: {e}")
