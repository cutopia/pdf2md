#!/usr/bin/env python3
import re

def restore_missing_letters(text):
    print(f"Input: {repr(text)}")
    
    # Pattern 11: "CASE le" should be "CASE file"
    result = re.sub(r'CASE le', 'CASE file', text)
    print(f"After CASE fix: {repr(result)}")
    
    return result

# Test with the exact text from the extraction
text = "STRENGTH   and EDUCATION.   C-A-S-E. A CASE le. Get it? Yeah, we're"
result = restore_missing_letters(text)
