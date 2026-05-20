#!/usr/bin/env python3
"""Test script to debug PDF text extraction"""

import pdfplumber

# Test with one of our PDFs
pdf_path = "sample_rpg_pdfs/Those_Dark_Places.pdf"

print(f"Testing PDF: {pdf_path}")

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    # Try first few pages with different settings
    for page_num in range(min(5, len(pdf.pages))):
        page = pdf.pages[page_num]
        
        print(f"\n=== Page {page_num + 1} ===")
        print(f"Dimensions: {page.width} x {page.height}")
        
        # Try default extraction
        try:
            text_default = page.extract_text()
            if text_default:
                print(f"Default extraction: {len(text_default)} chars")
                print("First 200 chars:", repr(text_default[:200]))
            else:
                print("No text with default settings")
        except Exception as e:
            print(f"Error with default: {e}")
        
        # Try with layout=True
        try:
            text_layout = page.extract_text(layout=True)
            if text_layout:
                print(f"With layout=True: {len(text_layout)} chars")
                print("First 200 chars:", repr(text_layout[:200]))
            else:
                print("No text with layout=True")
        except Exception as e:
            print(f"Error with layout: {e}")
        
        # Try tables
        try:
            tables = page.extract_tables()
            if tables:
                print(f"Found {len(tables)} table(s)")
                for i, table in enumerate(tables):
                    print(f"Table {i+1}: {len(table)} rows")
                    for row in table[:2]:  # Show first 2 rows
                        print(" ", row)
            else:
                print("No tables found")
        except Exception as e:
            print(f"Error with tables: {e}")
