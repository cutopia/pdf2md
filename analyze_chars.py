#!/usr/bin/env python3

# Read a sample line from the output as binary first to understand the encoding issue
with open('markdown_output/Those_Dark_Places.md', 'rb') as f:
    content_bytes = f.read()

# Find lines with corruption patterns
lines = content_bytes.split(b'\n')
for i, line in enumerate(lines[:20]):
    # Look for null bytes or unusual byte sequences
    if b'\x00' in line or b'\xef\xbc' in line:
        print(f"Line {i}: Found unusual bytes")
        # Show hex representation of first 50 bytes
        print(f"  Hex: {line[:50].hex()}")
        try:
            text = line.decode('utf-8', errors='replace')
            print(f"  Text: {repr(text)}")
        except:
            pass
