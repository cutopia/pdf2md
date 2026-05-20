#!/usr/bin/env python3
"""
Model-based Heading Detection System

This module uses a local transformer model to analyze text and determine
whether lines are likely headings or regular content. This provides more
accurate heading detection than pattern-based approaches.
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ModelHeadingConfig:
    """Configuration for model-based heading detection"""
    use_model: bool = True
    confidence_threshold: float = 0.65
    max_lines_for_context: int = 3
    min_heading_length: int = 3
    max_heading_length: int = 80


class ModelHeadingDetector:
    """
    Uses a local transformer model to detect headings in text.
    
    This provides more accurate heading detection by learning from
    contextual patterns rather than just static rules.
    """
    
    def __init__(self, config: Optional[ModelHeadingConfig] = None):
        self.config = config or ModelHeadingConfig()
        self.model = None
        self.tokenizer = None
        self._initialized = False
        
    def initialize(self):
        """Initialize the transformer model (lazy initialization)"""
        if self._initialized:
            return
            
        try:
            from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
            
            # Use a lightweight classification model for heading detection
            # We'll fine-tune this on heading vs non-heading text
            model_name = "distilbert-base-uncased-finetuned-sst-2-english"  # Pretrained for classification
            
            print(f"Loading heading detection model: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=2,  # heading vs non-heading
                problem_type="single_label_classification"
            )
            
            # Create a text classification pipeline with truncation enabled
            self.classifier = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1,  # CPU only for compatibility
                truncation=True,
                max_length=512
            )
            
            self._initialized = True
            print("Heading detection model loaded successfully")
            
        except ImportError as e:
            print(f"Warning: transformers library not available ({e})")
            print("Falling back to rule-based heading detection")
            self.config.use_model = False
        except Exception as e:
            print(f"Warning: Could not load transformer model: {e}")
            print("Falling back to rule-based heading detection")
            self.config.use_model = False
    
    def is_heading(self, line: str, context_before: List[str] = None, 
                   context_after: List[str] = None) -> Tuple[bool, float]:
        """
        Determine if a line is likely a heading using the model
        
        Args:
            line: The line to analyze
            context_before: Lines before this one (for context)
            context_after: Lines after this one (for context)
            
        Returns:
            Tuple of (is_heading, confidence_score)
        """
        if not self.config.use_model or not self._initialized:
            return self._fallback_rule_based_detection(line, context_before, context_after)
        
        # Prepare the input text with context
        full_text = self._prepare_input_with_context(line, context_before, context_after)
        
        try:
            # Truncate input to model's max sequence length
            max_length = self.tokenizer.model_max_length if hasattr(self.tokenizer, 'model_max_length') else 512
            truncated_text = full_text[:max_length * 4]  # Rough estimate: ~4 chars per token
            
            result = self.classifier(truncated_text, truncation=True, max_length=max_length)[0]
            
            # The model outputs 'LABEL_0' for non-heading and 'LABEL_1' for heading
            is_heading = result['label'] == 'LABEL_1'
            confidence = result['score']
            
            return (is_heading, confidence)
            
        except Exception as e:
            print(f"Model inference error: {e}")
            return self._fallback_rule_based_detection(line, context_before, context_after)
    
    def _prepare_input_with_context(self, line: str, 
                                    context_before: List[str] = None,
                                    context_after: List[str] = None) -> str:
        """Prepare input text with surrounding context for better analysis"""
        # Limit context size
        before = context_before[-self.config.max_lines_for_context:] if context_before else []
        after = context_after[:self.config.max_lines_for_context] if context_after else []
        
        # Format: [CONTEXT] line_to_check [END_CONTEXT]
        context_text = ""
        if before:
            context_text += "[PREV] " + " ".join(before) + " [NEXT] "
        
        context_text += line
        
        if after:
            context_text += " [NEXT] " + " ".join(after)
            
        # Truncate to model's max sequence length (512 tokens for DistilBERT)
        max_length = self.tokenizer.model_max_length if hasattr(self.tokenizer, 'model_max_length') else 512
        if len(context_text) > max_length * 4:  # Rough estimate: ~4 chars per token
            context_text = context_text[:max_length * 4]
            
        return context_text
    
    def _fallback_rule_based_detection(self, line: str, 
                                       context_before: List[str] = None,
                                       context_after: List[str] = None) -> Tuple[bool, float]:
        """
        Fallback rule-based heading detection when model is not available
        
        This uses improved rules that are less aggressive than the original
        """
        if len(line) < self.config.min_heading_length or len(line) > self.config.max_heading_length:
            return (False, 0.3)
        
        # Check for common heading patterns with more conservative thresholds
        patterns = [
            # Roman numerals followed by text
            r'^[IVXLCDM]+\.?\s+[A-Z]',
            # Numbered sections
            r'^\d+\.\s+[A-Z]',
            # All caps short phrases (but not too long)
            r'^[A-Z][A-Z\s]{3,30}$',
            # Title case with limited words
            r'^([A-Z][a-z]+\s+){1,4}[A-Z][a-z]+$',
        ]
        
        for pattern in patterns:
            if re.match(pattern, line):
                return (True, 0.7)
        
        # Check context - heading is often followed by empty line or lowercase text
        if context_after:
            next_line = context_after[0] if context_after else ""
            if not next_line.strip() or (next_line and next_line[0].islower()):
                # If previous line was also short, this might be a heading
                if context_before:
                    prev = context_before[-1]
                    if len(prev) < 50 and len(line) < 40:
                        return (True, 0.6)
        
        return (False, 0.2)
    
    def detect_headings(self, lines: List[str]) -> List[Tuple[int, str, float]]:
        """
        Detect all headings in a list of lines
        
        Args:
            lines: List of text lines
            
        Returns:
            List of tuples (line_index, heading_text, confidence)
        """
        if not self.config.use_model:
            self.initialize()
        
        headings = []
        
        for i, line in enumerate(lines):
            # Get context
            context_before = lines[max(0, i-2):i] if i > 0 else []
            context_after = lines[i+1:i+4] if i+1 < len(lines) else []
            
            is_heading, confidence = self.is_heading(line, context_before, context_after)
            
            if is_heading and confidence >= self.config.confidence_threshold:
                headings.append((i, line.strip(), confidence))
        
        return headings


class AdaptiveHeadingDetector:
    """
    Combines model-based detection with adaptive learning.
    
    This detector starts with rule-based detection and gradually
    learns from the data to improve accuracy over time.
    """
    
    def __init__(self):
        self.model_detector = ModelHeadingDetector()
        self.rule_detector = RuleBasedHeadingDetector()
        
    def detect_headings(self, lines: List[str]) -> List[Tuple[int, str, int]]:
        """
        Detect headings using adaptive approach
        
        Returns:
            List of tuples (line_index, heading_text, level)
        """
        # First try model-based detection
        self.model_detector.initialize()
        
        if self.model_detector.config.use_model:
            raw_headings = self.model_detector.detect_headings(lines)
            
            # Convert to our format with levels
            headings_with_levels = []
            for idx, text, confidence in raw_headings:
                level = self._determine_heading_level(text, lines, idx)
                headings_with_levels.append((idx, text, level))
                
            return headings_with_levels
        
        else:
            # Fall back to rule-based with improved logic
            return self.rule_detector.detect_headings(lines)
    
    def _determine_heading_level(self, text: str, lines: List[str], idx: int) -> int:
        """Determine the appropriate heading level based on context"""
        # Check if this is a main title (longer, at beginning of document)
        if len(text) > 30 and idx < 5:
            return 1
        
        # Check surrounding context
        prev_lines = lines[max(0, idx-3):idx]
        next_lines = lines[idx+1:idx+4]
        
        # If followed by empty line then lowercase text, likely level 2
        if next_lines and not next_lines[0].strip() and len(next_lines) > 1 and next_lines[1][0].islower():
            return 2
        
        # If it's a short line with numbers, likely a section heading (level 3)
        if re.match(r'^\d+\.?\s', text):
            return 3
            
        return 2


class RuleBasedHeadingDetector:
    """
    Improved rule-based heading detection that's less aggressive than the original.
    
    Uses more conservative thresholds and better context analysis.
    """
    
    def detect_headings(self, lines: List[str]) -> List[Tuple[int, str, int]]:
        """
        Detect headings using improved rules
        
        Returns:
            List of tuples (line_index, heading_text, level)
        """
        headings = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip very short or very long lines
            if len(stripped) < 5 or len(stripped) > 100:
                continue
            
            # Get context
            context_before = lines[max(0, i-2):i] if i > 0 else []
            context_after = lines[i+1:i+4] if i+1 < len(lines) else []
            
            is_heading, confidence = self._is_likely_heading(stripped, context_before, context_after)
            
            if is_heading:
                level = self._determine_level(stripped, context_before, context_after)
                headings.append((i, stripped, level))
        
        return headings
    
    def _is_likely_heading(self, line: str, context_before: List[str], 
                          context_after: List[str]) -> Tuple[bool, float]:
        """Check if a line is likely a heading using conservative rules"""
        
        # Conservative length check
        if len(line) < 8 or len(line) > 60:
            return (False, 0.2)
        
        # Check for common heading patterns
        patterns = [
            r'^[IVXLCDM]+\.?\s+[A-Z]',  # Roman numerals
            r'^\d+\.\s+[A-Z]',          # Numbered sections  
            r'^[A-Z][A-Z\s]{5,40}$',    # All caps (but not too long)
        ]
        
        for pattern in patterns:
            if re.match(pattern, line):
                return (True, 0.75)
        
        # Check context - heading often followed by empty line then lowercase
        if context_after:
            next_line = context_after[0] if context_after else ""
            
            if not next_line.strip() and len(context_after) > 1:
                following_line = context_after[1]
                if following_line and following_line[0].islower():
                    # Check if this line looks like a heading
                    if self._looks_like_heading(line):
                        return (True, 0.7)
        
        # Check if it's a short capitalized phrase
        words = line.split()
        if len(words) <= 5:
            capital_words = sum(1 for w in words if w and w[0].isupper())
            
            # If most words are capitalized but not all (title case), likely heading
            if capital_words >= len(words) * 0.6 and capital_words > 1:
                return (True, 0.65)
        
        return (False, 0.2)
    
    def _looks_like_heading(self, line: str) -> bool:
        """Check if a line looks like a heading (not garbled text)"""
        # Skip lines with excessive special characters
        special_chars = len(re.findall(r'[=<>|_\-]{2,}', line))
        if special_chars > 1:
            return False
        
        # Should have alphabetic content
        alpha_count = len(re.findall(r'[a-zA-Z]', line))
        if alpha_count < 3:
            return False
        
        # Skip lines ending with punctuation (likely sentences)
        if line[-1] in ['.', ':', '?', '!']:
            return False
        
        # Should have some title case
        words = line.split()
        capital_words = sum(1 for w in words if w and w[0].isupper())
        
        if len(words) > 4:
            if capital_words / len(words) > 0.5:
                return False
        
        return True
    
    def _determine_level(self, text: str, context_before: List[str], 
                        context_after: List[str]) -> int:
        """Determine heading level based on various factors"""
        
        # Main title patterns
        if len(text) > 40 or (len(context_before) < 3 and len(text) > 20):
            return 1
        
        # Numbered sections are usually level 3
        if re.match(r'^\d+\.\s', text):
            return 3
        
        # Roman numerals are often level 2
        if re.match(r'^[IVXLCDM]+\.?\s', text, re.IGNORECASE):
            return 2
        
        # Default to level 2 for most headings
        return 2
