"""
Fast Text Filter for Layer 1 processing
Uses better-profanity library for quick banned word detection
"""

import re
import time
from typing import List, Set, Tuple, Optional
from better_profanity import profanity
from shared.enhanced_types import FilterResult, HarmCategory

class FastTextFilter:
    def __init__(self):
        # Initialize profanity filter
        profanity.load_censor_words()
        
        # Additional custom banned words/patterns
        self.custom_banned_words = {
            'hate_speech': [
                'nazi', 'fascist', 'terrorist', 'genocide', 'ethnic cleansing',
                'supremacist', 'jihad', 'infidel', 'subhuman'
            ],
            'violence': [
                'kill yourself', 'kys', 'suicide', 'murder', 'assassinate', 
                'bomb', 'explosive', 'weapon', 'gun', 'knife attack'
            ],
            'harassment': [
                'doxx', 'dox', 'swat', 'harass', 'stalk', 'cyberbully',
                'blackmail', 'extort', 'threaten'
            ],
            'illegal_activity': [
                'drug deal', 'sell drugs', 'buy drugs', 'money laundering',
                'fraud', 'scam', 'illegal download', 'piracy', 'hacking'
            ],
            'spam': [
                'click here', 'free money', 'get rich quick', 'mlm',
                'pyramid scheme', 'investment opportunity', 'guaranteed profit'
            ]
        }
        
        # Compile patterns for faster matching
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for faster matching"""
        self.compiled_patterns = {}
        for category, words in self.custom_banned_words.items():
            # Create word boundary patterns to avoid false positives
            patterns = [rf'\b{re.escape(word.lower())}\b' for word in words]
            self.compiled_patterns[category] = re.compile('|'.join(patterns), re.IGNORECASE)
    
    def add_custom_words(self, category: str, words: List[str]):
        """Add custom banned words to specific category"""
        if category not in self.custom_banned_words:
            self.custom_banned_words[category] = []
        
        self.custom_banned_words[category].extend(words)
        self._compile_patterns()
    
    def filter_text(self, text: str) -> FilterResult:
        """
        Fast text filtering using multiple methods
        Returns FilterResult with detected issues
        """
        start_time = time.time()
        
        if not text or not text.strip():
            return FilterResult(processing_time_ms=(time.time() - start_time) * 1000)
        
        text_lower = text.lower().strip()
        found_categories = set()
        banned_words_found = []
        confidence_scores = []
        
        # 1. Check for profanity using better-profanity
        if profanity.contains_profanity(text):
            found_categories.add(HarmCategory.PROFANITY)
            confidence_scores.append(0.8)
            # Extract actual profane words
            censored = profanity.censor(text, censor='***')
            banned_words_found.extend(self._extract_censored_words(text, censored))
        
        # 2. Check custom patterns for specific categories
        for category_name, pattern in self.compiled_patterns.items():
            matches = pattern.findall(text_lower)
            if matches:
                category_enum = self._get_harm_category(category_name)
                if category_enum:
                    found_categories.add(category_enum)
                    banned_words_found.extend(matches)
                    # Higher confidence for exact pattern matches
                    confidence_scores.append(0.9)
        
        # 3. Additional heuristics
        additional_confidence = self._apply_heuristics(text_lower)
        if additional_confidence > 0:
            confidence_scores.append(additional_confidence)
        
        # Calculate overall confidence
        overall_confidence = max(confidence_scores) if confidence_scores else 0.0
        is_harmful = len(found_categories) > 0
        
        processing_time = (time.time() - start_time) * 1000
        
        details = None
        if banned_words_found:
            details = f"Banned words found: {', '.join(set(banned_words_found[:5]))}"
        
        return FilterResult(
            is_harmful=is_harmful,
            confidence=overall_confidence,
            categories=list(found_categories),
            details=details,
            processing_time_ms=processing_time
        )
    
    def _extract_censored_words(self, original: str, censored: str) -> List[str]:
        """Extract words that were censored by profanity filter"""
        original_words = original.split()
        censored_words = censored.split()
        
        found_words = []
        for orig, cens in zip(original_words, censored_words):
            if '*' in cens and orig.lower() != cens.lower():
                found_words.append(orig.lower())
        
        return found_words
    
    def _get_harm_category(self, category_name: str) -> Optional[HarmCategory]:
        """Convert string category to HarmCategory enum"""
        category_map = {
            'hate_speech': HarmCategory.HATE_SPEECH,
            'violence': HarmCategory.VIOLENCE,
            'harassment': HarmCategory.HARASSMENT,
            'illegal_activity': HarmCategory.ILLEGAL_ACTIVITY,
            'spam': HarmCategory.SPAM
        }
        return category_map.get(category_name)
    
    def _apply_heuristics(self, text: str) -> float:
        """Apply additional heuristic rules"""
        confidence = 0.0
        
        # Check for excessive capitalization (potential spam/harassment)
        if len(text) > 10:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.6:
                confidence = max(confidence, 0.4)
        
        # Check for repeated characters (spam indicator)
        if re.search(r'(.)\1{4,}', text):  # 5+ repeated chars
            confidence = max(confidence, 0.3)
        
        # Check for suspicious URLs patterns
        if re.search(r'bit\.ly|tinyurl|t\.co|\w+\.tk|\w+\.ml', text, re.IGNORECASE):
            confidence = max(confidence, 0.5)
        
        return confidence
    
    def is_text_suspicious(self, text: str) -> Tuple[bool, float]:
        """Quick suspicious text check without full analysis"""
        if not text:
            return False, 0.0
            
        result = self.filter_text(text)
        return result.is_harmful, result.confidence 