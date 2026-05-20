#!/usr/bin/env python3
import pdfplumber

pdf_path = "sample_rpg_pdfs/Those_Dark_Places.pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]
    
    # Get the page as an image
    im = page.to_image(resolution=150)
    
    if hasattr(im, 'original'):
        print(f"Image size: {im.original.size}")
        
        # Try to extract text using OCR
        try:
            import pytesseract
            
            img = im.original.convert('L')
            text = pytesseract.image_to_string(img)
            
            print(f"\nOCR extracted: {len(text)} chars")
            print("First 500 chars:", repr(text[:500]))
            
            # Check for special characters
            special_chars = {}
            for i, char in enumerate(text):
                code = ord(char)
                if code > 255 or (code < 32 and code != 10 and code != 13 and code != 9):
                    if char not in special_chars:
                        special_chars[char] = []
                    special_chars[char].append((i, repr(text[max(0,i-10):min(len(text),i+10)])))
            
            print(f"\nFound {len(special_chars)} unique special characters:")
            for char, occurrences in list(special_chars.items())[:10]:
                code = ord(char)
                print(f"  U+{code:04X}: {repr(char)} - {len(occurrences)} occurrences")
                
        except ImportError:
            print("pytesseract not available")
