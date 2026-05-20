#!/usr/bin/env python3

# Let's trace through the conversion process to see where "CASE le" comes from
import sys
sys.path.insert(0, '/home/dev/pdf2md')

import pdfplumber

pdf_path = "sample_rpg_pdfs/Those_Dark_Places.pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[61]  # Page 62 (0-indexed)
    
    print(f"Page 62 dimensions: {page.width} x {page.height}")
    
    # Try regular extraction
    text = page.extract_text()
    if text:
        print(f"Regular extraction: {len(text)} chars")
        if 'CASE' in text:
            idx = text.find('CASE')
            print(f"Found CASE at pos {idx}: {text[max(0,idx-20):min(len(text),idx+50)]}")
    else:
        print("No regular text extracted")
