#!/usr/bin/env python3
from PyPDF2 import PdfReader

pdf_path = "sample_rpg_pdfs/Those_Dark_Places.pdf"

reader = PdfReader(pdf_path)
print(f"Total pages: {len(reader.pages)}")

# Try to extract text from page 1
page = reader.pages[0]
text = page.extract_text()

if text:
    print(f"Extracted: {len(text)} chars")
    
    # Look for null bytes and special characters
    for i, char in enumerate(text[:500]):
        code = ord(char)
        if code > 255 or (code < 32 and code != 10 and code != 13):
            print(f"Char at {i}: U+{code:04X} = {repr(char)}")
else:
    print("No text extracted with PyPDF2")
