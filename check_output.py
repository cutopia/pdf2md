#!/usr/bin/env python3

with open('markdown_output/Those_Dark_Places.md', 'rb') as f:
    content = f.read()

# Find lines with corruption patterns
lines = content.split(b'\n')
for i, line in enumerate(lines):
    if b'science' in line or b'reects' in line or b'The Attributes' in line:
        print(f"Line {i}:")
        print(f"  Hex: {line[:100].hex()}")
        try:
            text = line.decode('utf-8', errors='replace')
            print(f"  Text: {repr(text)}")
        except:
            pass
