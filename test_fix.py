#!/usr/bin/env python3

# Test the corruption patterns
text = "science-\x00ction cinema. \ue053e movie"

print("Original text:")
print(repr(text))

# Try to fix null bytes
fixed = text.replace('\x00', '')
print("\nAfter removing null bytes:")
print(repr(fixed))

# Try to fix Unicode character
import re
def fix_char(char):
    corruption_map = {
        '\ue053': 'Th',
    }
    return corruption_map.get(char, '')

# Test the regex approach
result = re.sub(r'[^\x00-\x7F]', lambda m: fix_char(m.group(0)), fixed)
print("\nAfter fixing Unicode chars:")
print(repr(result))
