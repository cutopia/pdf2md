#!/usr/bin/env python3

with open('markdown_output/Those_Dark_Places.md', 'rb') as f:
    content = f.read()

# Find the "CASE" line
lines = content.split(b'\n')
for i, line in enumerate(lines):
    if b'CASE' in line and b'le' in line:
        print(f"Line {i}:")
        print(f"Hex: {line.hex()}")
        
        # Look for null bytes around "CASE"
        idx = line.find(b'CASE')
        if idx >= 0:
            print(f"'CASE' found at byte {idx}")
            print(f"Bytes after CASE: {line[idx+4:idx+10].hex()}")
