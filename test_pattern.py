#!/usr/bin/env python3
import re

# Test with exact text from file (with null byte)
text = "have a CASE \x00le which consists"

print("Original:", repr(text))

# Check the bytes around CASE
idx = text.find('CASE')
if idx >= 0:
    print(f"Bytes around CASE: {text[idx:idx+10].encode('utf-8', errors='replace').hex()}")
    
# Try matching with space before null byte
pattern1 = r'CASE \x00le'
match1 = re.search(pattern1, text)
print(f"Pattern {repr(pattern1)}: {match1}")
