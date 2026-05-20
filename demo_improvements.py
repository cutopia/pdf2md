#!/usr/bin/env python3
"""
Demonstration of heading detection improvements.

This script shows how the improved detector handles various text patterns
more accurately than the original over-aggressive approach.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from model_heading_detector import RuleBasedHeadingDetector


def demonstrate_improvements():
    """Demonstrate the improvements with examples"""
    
    print("="*70)
    print("HEADING DETECTION IMPROVEMENTS DEMONSTRATION")
    print("="*70)
    
    # Example 1: Text that was incorrectly marked as headings
    print("\n1. PROBLEM CASES (Previously over-detected):")
    print("-" * 70)
    
    problematic_text = """
This is a paragraph that starts with a capital letter.
It contains multiple sentences and ends with proper punctuation.

Another paragraph that begins with an uppercase word.
The text continues normally here with more content.

E The End
This line was incorrectly marked as a heading before.
It's actually just a sentence starting with "The End".

1. Introduction
This is a numbered list item, not a heading.
"""
    
    lines = [line.strip() for line in problematic_text.split('\n') if line.strip()]
    
    detector = RuleBasedHeadingDetector()
    headings = detector.detect_headings(lines)
    
    print(f"Text with {len(lines)} lines")
    print(f"Lines marked as headings: {len(headings)} (should be 0-1)")
    
    for idx, line, level in headings:
        print(f"   Line {idx}: '{line[:60]}...' [Level {level}]")
    
    # Example 2: Text with actual headings
    print("\n2. CORRECT CASES (Properly detected):")
    print("-" * 70)
    
    proper_text = """
Chapter 1: The Beginning

This is the first chapter of our adventure.

Section 1.1: Introduction

In this section, we introduce basic concepts.
The rules are designed to be easy to learn.

 subsection A: Advanced Topics

For experienced players, there are advanced strategies.

Chapter 2: Combat Rules

Combat is a central part of the game.
"""
    
    lines = [line.strip() for line in proper_text.split('\n') if line.strip()]
    headings = detector.detect_headings(lines)
    
    print(f"Text with {len(lines)} lines")
    print(f"Lines marked as headings: {len(headings)} (should be 4-5)")
    
    for idx, line, level in headings:
        print(f"   Line {idx}: '{line[:60]}...' [Level {level}]")
    
    # Example 3: Real-world PDF text
    print("\n3. REAL-WORLD EXAMPLE:")
    print("-" * 70)
    
    real_text = """
Soest STTRIAL SCENE Ee FIco Tl oN

ROLEPLAYING

GAME SYSTEM

This is the beginning of our adventure.
The rules will be explained in detail below.

1. Character Creation

Before you begin playing, you need to create your character.
Follow these steps carefully:

 subsection A: Attributes

Your character has several attributes that define their abilities.
These include strength, dexterity, and intelligence.
"""
    
    lines = [line.strip() for line in real_text.split('\n') if line.strip()]
    headings = detector.detect_headings(lines)
    
    print(f"Text with {len(lines)} lines")
    print(f"Lines marked as headings: {len(headings)}")
    
    for idx, line, level in headings:
        print(f"   Line {idx}: '{line[:60]}...' [Level {level}]")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY OF IMPROVEMENTS:")
    print("="*70)
    print("""
1. Conservative Length Thresholds:
   - Minimum: 8 characters (was 3)
   - Maximum: 60 characters (was 40)
   
2. Better Context Analysis:
   - Considers multiple lines before/after
   - Checks if followed by empty line + lowercase text
   
3. Pattern Matching with Confidence:
   - Roman numerals: high confidence
   - Numbered sections: medium-high confidence  
   - Title case phrases: medium confidence
   
4. Reduced False Positives:
   - Paragraphs not marked as headings
   - Sentences with punctuation ignored
   - Short lines filtered out

5. Adaptive Detection:
   - Can use model or rules based on availability
   - Graceful degradation if model unavailable
""")
    
    print("="*70)


def compare_approaches():
    """Compare original vs improved approach"""
    
    test_text = """
This is a paragraph that starts with capital letters.
It contains multiple sentences and proper punctuation.

Chapter 1: The Beginning

This is the first chapter content.
More text follows here.

Section 1.1: Introduction

Introduction content goes here.
"""
    
    lines = [line.strip() for line in test_text.split('\n') if line.strip()]
    
    print("\nCOMPARISON: Original vs Improved")
    print("="*70)
    
    detector = RuleBasedHeadingDetector()
    headings = detector.detect_headings(lines)
    
    print(f"\nOriginal approach would mark ~8-10 lines as headings (over-aggressive)")
    print(f"Improved approach marks {len(headings)} lines as headings (conservative)")
    
    print("\nImproved detection results:")
    for idx, line, level in headings:
        # Determine if this is likely correct
        is_likely_correct = any(pattern in line.lower() 
                               for pattern in ['chapter', 'section', 'intro'])
        
        status = "✓" if is_likely_correct else "?"
        print(f"   {status} Line {idx}: '{line[:50]}...' [Level {level}]")


if __name__ == "__main__":
    demonstrate_improvements()
    compare_approaches()
