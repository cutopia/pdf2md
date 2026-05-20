#!/usr/bin/env python3
"""
Test script for heading detection improvements.
Compares original vs improved heading detection on sample text.
"""

import sys
from pathlib import Path

# Add the project directory to path
sys.path.insert(0, str(Path(__file__).parent))

from model_heading_detector import (
    ModelHeadingDetector,
    RuleBasedHeadingDetector,
    AdaptiveHeadingDetector
)


def test_sample_text():
    """Test with sample RPG rulebook text"""
    
    # Sample text that mimics RPG rulebook structure
    sample_text = """
Chapter 1: The Beginning

This is the first chapter of our adventure. It contains important rules and guidelines.

Section 1.1: Introduction

In this section, we introduce the basic concepts of the game.
The rules are designed to be easy to learn but hard to master.

 subsection A: Advanced Topics

For experienced players, there are advanced strategies and techniques.

Chapter 2: Combat Rules

Combat is a central part of the game. Here are the core mechanics.

Section 2.1: Attack Mechanics

When you attack, roll a d20 and add your modifier.
If the result meets or exceeds the target's defense, you hit.

 subsection B: Special Attacks

Some attacks have special effects or conditions.
"""
    
    lines = [line.strip() for line in sample_text.split('\n') if line.strip()]
    
    print("="*60)
    print("HEADING DETECTION COMPARISON")
    print("="*60)
    
    # Test with rule-based detector
    print("\n1. Rule-Based Detection (Improved):")
    print("-" * 40)
    rule_detector = RuleBasedHeadingDetector()
    rule_headings = rule_detector.detect_headings(lines)
    
    for idx, line, level in rule_headings:
        print(f"   Line {idx}: '{line[:50]}...' [Level {level}]")
    
    # Test with model-based detector
    print("\n2. Model-Based Detection (DistilBERT):")
    print("-" * 40)
    try:
        model_detector = ModelHeadingDetector()
        model_detector.initialize()
        model_headings = model_detector.detect_headings(lines)
        
        for idx, line, confidence in model_headings:
            print(f"   Line {idx}: '{line[:50]}...' [Confidence: {confidence:.2f}]")
    except Exception as e:
        print(f"   Model detection failed: {e}")
    
    # Test with adaptive detector
    print("\n3. Adaptive Detection (Hybrid):")
    print("-" * 40)
    try:
        adaptive_detector = AdaptiveHeadingDetector()
        adaptive_headings = adaptive_detector.detect_headings(lines)
        
        for idx, line, level in adaptive_headings:
            print(f"   Line {idx}: '{line[:50]}...' [Level {level}]")
    except Exception as e:
        print(f"   Adaptive detection failed: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total lines analyzed: {len(lines)}")
    print(f"Rule-based headings found: {len(rule_headings)}")
    try:
        print(f"Model-based headings found: {len(model_headings)}")
        print(f"Adaptive headings found: {len(adaptive_headings)}")
    except:
        pass
    
    # Expected headings in our sample
    expected_headings = [
        "Chapter 1: The Beginning",
        "Section 1.1: Introduction", 
        "subsection A: Advanced Topics",
        "Chapter 2: Combat Rules",
        "Section 2.1: Attack Mechanics",
        "subsection B: Special Attacks"
    ]
    
    print(f"\nExpected headings: {len(expected_headings)}")
    print("Note: Detection accuracy depends on text quality and context")


def test_real_pdf():
    """Test with actual PDF file if available"""
    
    pdf_path = Path(__file__).parent / "sample_rpg_pdfs" / "Those_Dark_Places.pdf"
    
    if not pdf_path.exists():
        print(f"\nPDF not found at {pdf_path}")
        return
    
    try:
        import pdfplumber
        import pytesseract
        
        with pdfplumber.open(str(pdf_path)) as pdf:
            page = pdf.pages[0]
            
            # Try text extraction
            text = page.extract_text()
            
            if not text or len(text.strip()) < 20:
                print("\nText extraction failed, trying OCR...")
                
                im = page.to_image(resolution=150)
                img = im.original.convert('L')
                text = pytesseract.image_to_string(img)
            
            lines = [line for line in text.split('\n') if line.strip()]
            
            print(f"\nReal PDF Analysis ({len(lines)} lines):")
            print("-" * 40)
            
            # Use rule-based detector
            detector = RuleBasedHeadingDetector()
            headings = detector.detect_headings(lines)
            
            print(f"Found {len(headings)} potential headings:")
            for idx, line, level in headings[:5]:
                print(f"   Line {idx}: '{line[:60]}...' [Level {level}]")
                
    except Exception as e:
        print(f"\nError analyzing PDF: {e}")


def main():
    """Run all tests"""
    
    print("\nHeading Detection Test Suite")
    print("="*60)
    
    test_sample_text()
    test_real_pdf()
    
    print("\n" + "="*60)
    print("Tests complete!")
    print("="*60)


if __name__ == "__main__":
    main()
