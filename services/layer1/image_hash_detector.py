"""
Image Hash Detector for Layer 1 processing
Uses perceptual hashing to detect known harmful images quickly
"""

import time
import hashlib
from typing import List, Dict, Set, Optional, Tuple
from io import BytesIO
import imagehash
from PIL import Image
from shared.enhanced_types import FilterResult, HarmCategory

class ImageHashDetector:
    def __init__(self):
        # Known harmful image hashes database (in production, this would be loaded from a database)
        self.harmful_hashes = {
            # Example format: hash -> (category, confidence)
            # These would be populated from a real database of known harmful content
        }
        
        # NSFW/inappropriate content indicators
        self.suspicious_patterns = {
            'high_skin_tone_ratio': HarmCategory.SEXUAL_CONTENT,
            'violence_indicators': HarmCategory.VIOLENCE,
            'hate_symbols': HarmCategory.HATE_SPEECH
        }
        
        # Hash algorithms to use
        self.hash_algorithms = {
            'phash': imagehash.phash,
            'dhash': imagehash.dhash,
            'ahash': imagehash.average_hash,
            'whash': imagehash.whash
        }
        
        # Similarity thresholds for different hash types
        self.similarity_thresholds = {
            'phash': 5,  # Higher threshold for perceptual hash
            'dhash': 3,
            'ahash': 8,
            'whash': 5
        }
    
    def add_harmful_hash(self, image_hash: str, category: HarmCategory, confidence: float = 0.9):
        """Add a known harmful image hash to the database"""
        self.harmful_hashes[image_hash] = (category, confidence)
    
    def load_harmful_hashes_from_db(self, hash_database: Dict[str, Tuple[HarmCategory, float]]):
        """Load harmful hashes from external database"""
        self.harmful_hashes.update(hash_database)
    
    def analyze_image(self, image_data: bytes) -> FilterResult:
        """
        Analyze image using multiple hash algorithms and pattern detection
        Returns FilterResult with detected issues
        """
        start_time = time.time()
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            found_categories = set()
            confidence_scores = []
            hash_matches = []
            
            # 1. Calculate multiple hash types
            image_hashes = self._calculate_hashes(image)
            
            # 2. Check against known harmful hashes
            for hash_type, img_hash in image_hashes.items():
                matches = self._find_similar_hashes(str(img_hash), hash_type)
                if matches:
                    for match_hash, (category, confidence) in matches:
                        found_categories.add(category)
                        confidence_scores.append(confidence)
                        hash_matches.append(f"{hash_type}:{match_hash}")
            
            # 3. Apply basic content analysis heuristics
            heuristic_confidence = self._apply_image_heuristics(image)
            if heuristic_confidence > 0:
                confidence_scores.append(heuristic_confidence)
                found_categories.add(HarmCategory.SEXUAL_CONTENT)  # Default assumption
            
            # Calculate overall results
            overall_confidence = max(confidence_scores) if confidence_scores else 0.0
            is_harmful = len(found_categories) > 0
            
            processing_time = (time.time() - start_time) * 1000
            
            details = None
            if hash_matches:
                details = f"Hash matches found: {', '.join(hash_matches[:3])}"
            
            return FilterResult(
                is_harmful=is_harmful,
                confidence=overall_confidence,
                categories=list(found_categories),
                details=details,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return FilterResult(
                is_harmful=False,
                confidence=0.0,
                details=f"Error processing image: {str(e)}",
                processing_time_ms=processing_time
            )
    
    def _calculate_hashes(self, image: Image.Image) -> Dict[str, str]:
        """Calculate multiple types of perceptual hashes"""
        hashes = {}
        
        try:
            for hash_name, hash_func in self.hash_algorithms.items():
                hashes[hash_name] = str(hash_func(image))
        except Exception as e:
            # Handle any errors in hash calculation
            pass
            
        return hashes
    
    def _find_similar_hashes(self, target_hash: str, hash_type: str) -> List[Tuple[str, Tuple[HarmCategory, float]]]:
        """Find similar hashes in the harmful database"""
        matches = []
        threshold = self.similarity_thresholds.get(hash_type, 5)
        
        try:
            target_hash_obj = imagehash.hex_to_hash(target_hash)
            
            for known_hash_str, (category, confidence) in self.harmful_hashes.items():
                if known_hash_str.startswith(f"{hash_type}:"):
                    known_hash = known_hash_str.split(":", 1)[1]
                    try:
                        known_hash_obj = imagehash.hex_to_hash(known_hash)
                        distance = target_hash_obj - known_hash_obj
                        
                        if distance <= threshold:
                            # Adjust confidence based on distance
                            distance_confidence = max(0.1, 1.0 - (distance / threshold))
                            adjusted_confidence = confidence * distance_confidence
                            matches.append((known_hash_str, (category, adjusted_confidence)))
                    except:
                        continue
                        
        except Exception:
            pass
            
        return matches
    
    def _apply_image_heuristics(self, image: Image.Image) -> float:
        """Apply basic heuristic analysis to detect potentially inappropriate content"""
        confidence = 0.0
        
        try:
            # Get image dimensions
            width, height = image.size
            
            # Skip very small images (likely not harmful content)
            if width < 50 or height < 50:
                return 0.0
            
            # Basic skin tone detection (very simple heuristic)
            skin_confidence = self._detect_skin_tone_ratio(image)
            confidence = max(confidence, skin_confidence)
            
            # Check image entropy (low entropy might indicate simple/generated content)
            entropy_confidence = self._analyze_image_entropy(image)
            confidence = max(confidence, entropy_confidence)
            
        except Exception:
            pass
            
        return confidence
    
    def _detect_skin_tone_ratio(self, image: Image.Image) -> float:
        """Simple skin tone detection using color analysis"""
        try:
            # Resize for faster processing
            small_image = image.resize((64, 64))
            pixels = list(small_image.getdata())
            
            skin_pixels = 0
            total_pixels = len(pixels)
            
            for r, g, b in pixels:
                # Simple skin tone detection (very basic heuristic)
                if (r > 95 and g > 40 and b > 20 and 
                    max(r, g, b) - min(r, g, b) > 15 and 
                    abs(r - g) > 15 and r > g and r > b):
                    skin_pixels += 1
            
            skin_ratio = skin_pixels / total_pixels
            
            # High skin ratio might indicate inappropriate content
            if skin_ratio > 0.6:
                return min(0.7, skin_ratio)
            elif skin_ratio > 0.4:
                return min(0.4, skin_ratio * 0.5)
                
        except Exception:
            pass
            
        return 0.0
    
    def _analyze_image_entropy(self, image: Image.Image) -> float:
        """Analyze image entropy for content detection"""
        try:
            # Convert to grayscale for entropy calculation
            gray_image = image.convert('L')
            small_image = gray_image.resize((32, 32))
            
            # Calculate histogram
            histogram = small_image.histogram()
            
            # Calculate entropy
            total_pixels = sum(histogram)
            entropy = 0.0
            
            for count in histogram:
                if count > 0:
                    probability = count / total_pixels
                    entropy -= probability * (probability.bit_length() - 1)
            
            # Very low entropy might indicate suspicious content
            if entropy < 2.0:
                return 0.3
                
        except Exception:
            pass
            
        return 0.0
    
    def get_image_fingerprint(self, image_data: bytes) -> Dict[str, str]:
        """Get all hash fingerprints for an image"""
        try:
            image = Image.open(BytesIO(image_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return self._calculate_hashes(image)
        except Exception:
            return {}
    
    def is_image_suspicious(self, image_data: bytes) -> Tuple[bool, float]:
        """Quick suspicious image check without full analysis"""
        result = self.analyze_image(image_data)
        return result.is_harmful, result.confidence 