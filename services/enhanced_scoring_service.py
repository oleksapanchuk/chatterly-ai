"""
Enhanced Scoring Service - Layer 3 Mathematical Model
Calculates comprehensive harm scores using weighted algorithms
"""

import math
import time
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass

from shared.enhanced_types import (
    ContentType, Layer1Result, Layer2Result, Layer3Result,
    HarmCategory, FilterResult, ContentWeights, LayerWeights,
    ProcessingConfig
)

@dataclass
class CategorySeverityWeights:
    """Severity weights for different harm categories"""
    PROFANITY: float = 0.6
    HATE_SPEECH: float = 0.95
    VIOLENCE: float = 0.9
    SEXUAL_CONTENT: float = 0.75
    HARASSMENT: float = 0.85
    SELF_HARM: float = 0.95
    ILLEGAL_ACTIVITY: float = 0.9
    SPAM: float = 0.4
    TOXIC_BEHAVIOR: float = 0.7

class EnhancedScoringService:
    def __init__(self):
        self.category_weights = CategorySeverityWeights()
        self.confidence_threshold = 0.1  # Minimum confidence to consider
        
    def calculate_comprehensive_score(
        self,
        layer1_results: Dict[ContentType, Layer1Result],
        layer2_results: Dict[ContentType, Layer2Result],
        config: ProcessingConfig
    ) -> Layer3Result:
        """
        Calculate comprehensive harm score using mathematical model
        
        Formula:
        Overall_Score = Σ(Content_Weight_i × Layer_Score_i)
        
        Where:
        Layer_Score_i = (Layer1_Weight × Layer1_Score_i) + (Layer2_Weight × Layer2_Score_i)
        Layer_Score_i = Category_Score × Confidence_Multiplier × Severity_Weight
        """
        start_time = time.time()
        
        # Normalize weights
        config.content_weights.normalize()
        config.layer_weights.normalize()
        
        # Calculate scores for each content type
        content_scores = {}
        all_categories = set()
        layer_details = {}
        
        # Process each content type
        content_types = set(layer1_results.keys()) | set(layer2_results.keys())
        
        for content_type in content_types:
            layer1_result = layer1_results.get(content_type)
            layer2_result = layer2_results.get(content_type)
            
            content_score, categories, details = self._calculate_content_score(
                layer1_result, layer2_result, config.layer_weights
            )
            
            content_scores[content_type] = content_score
            all_categories.update(categories)
            layer_details[content_type.value] = details
        
        # Calculate weighted overall score
        overall_score = self._calculate_weighted_overall_score(
            content_scores, config.content_weights
        )
        
        # Determine if content is harmful
        is_harmful = overall_score >= config.harm_threshold
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            layer1_results, layer2_results
        )
        
        # Create detailed calculation explanation
        calculation_details = self._create_calculation_details(
            content_scores, config, overall_score, layer_details
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return Layer3Result(
            overall_harm_score=round(overall_score, 2),
            is_harmful=is_harmful,
            harm_categories=list(all_categories),
            confidence=round(overall_confidence, 3),
            layer_scores=layer_details,
            calculation_details=calculation_details
        )
    
    def _calculate_content_score(
        self, 
        layer1_result: Optional[Layer1Result],
        layer2_result: Optional[Layer2Result],
        layer_weights: LayerWeights
    ) -> Tuple[float, Set[HarmCategory], str]:
        """Calculate score for a specific content type"""
        
        layer1_score = 0.0
        layer2_score = 0.0
        all_categories = set()
        
        # Layer 1 score calculation
        if layer1_result and layer1_result.fast_filter_result.confidence >= self.confidence_threshold:
            layer1_score, l1_categories = self._calculate_layer_score(
                layer1_result.fast_filter_result
            )
            all_categories.update(l1_categories)
        
        # Layer 2 score calculation  
        if layer2_result and layer2_result.ai_analysis_result.confidence >= self.confidence_threshold:
            layer2_score, l2_categories = self._calculate_layer_score(
                layer2_result.ai_analysis_result
            )
            all_categories.update(l2_categories)
        
        # Weighted combination of layer scores
        combined_score = (
            layer_weights.layer1_weight * layer1_score +
            layer_weights.layer2_weight * layer2_score
        )
        
        # Apply category amplification if multiple serious categories detected
        amplified_score = self._apply_category_amplification(combined_score, all_categories)
        
        details = f"L1: {layer1_score:.1f}, L2: {layer2_score:.1f}, Combined: {amplified_score:.1f}"
        
        return amplified_score, all_categories, details
    
    def _calculate_layer_score(self, filter_result: FilterResult) -> Tuple[float, Set[HarmCategory]]:
        """
        Calculate score for a single layer result
        
        Formula:
        Layer_Score = Σ(Category_Severity_Weight × Confidence_Multiplier) × 100
        Confidence_Multiplier = min(1.0, confidence × 1.2)  # Slight confidence boost
        """
        if not filter_result.is_harmful:
            return 0.0, set()
        
        categories = set(filter_result.categories)
        total_score = 0.0
        
        # Calculate confidence multiplier
        confidence_multiplier = min(1.0, filter_result.confidence * 1.2)
        
        for category in categories:
            severity_weight = getattr(self.category_weights, category.value.upper(), 0.5)
            category_score = severity_weight * confidence_multiplier * 100
            total_score += category_score
        
        # Apply diminishing returns for multiple categories
        if len(categories) > 1:
            total_score *= (1.0 + 0.1 * (len(categories) - 1))  # 10% bonus per additional category
        
        return min(100.0, total_score), categories
    
    def _apply_category_amplification(self, base_score: float, categories: Set[HarmCategory]) -> float:
        """
        Apply amplification based on category combinations
        
        Certain combinations of categories are particularly concerning:
        - Violence + Hate Speech = +20% amplification
        - Self Harm + any other = +15% amplification  
        - 3+ different categories = +10% amplification
        """
        amplified_score = base_score
        
        # Check for dangerous combinations
        if (HarmCategory.VIOLENCE in categories and 
            HarmCategory.HATE_SPEECH in categories):
            amplified_score *= 1.2  # 20% increase
        
        if HarmCategory.SELF_HARM in categories and len(categories) > 1:
            amplified_score *= 1.15  # 15% increase
        
        if len(categories) >= 3:
            amplified_score *= 1.1  # 10% increase for multiple categories
        
        return min(100.0, amplified_score)
    
    def _calculate_weighted_overall_score(
        self,
        content_scores: Dict[ContentType, float],
        content_weights: ContentWeights
    ) -> float:
        """
        Calculate weighted overall score across all content types
        
        Formula:
        Overall_Score = (Text_Weight × Text_Score) + 
                       (Image_Weight × Image_Score) + 
                       (Audio_Weight × Audio_Score)
        """
        overall_score = 0.0
        
        # Apply content type weights
        if ContentType.TEXT in content_scores:
            overall_score += content_weights.text_weight * content_scores[ContentType.TEXT]
        
        if ContentType.IMAGE in content_scores:
            overall_score += content_weights.image_weight * content_scores[ContentType.IMAGE]
        
        if ContentType.AUDIO in content_scores:
            overall_score += content_weights.audio_weight * content_scores[ContentType.AUDIO]
        
        return min(100.0, overall_score)
    
    def _calculate_overall_confidence(
        self,
        layer1_results: Dict[ContentType, Layer1Result],
        layer2_results: Dict[ContentType, Layer2Result]
    ) -> float:
        """
        Calculate overall confidence using weighted harmonic mean
        Harmonic mean is less sensitive to outliers than arithmetic mean
        """
        confidences = []
        weights = []
        
        # Collect confidence scores and their weights
        for content_type in set(layer1_results.keys()) | set(layer2_results.keys()):
            layer1_result = layer1_results.get(content_type)
            layer2_result = layer2_results.get(content_type)
            
            if layer1_result and layer1_result.fast_filter_result.confidence > 0:
                confidences.append(layer1_result.fast_filter_result.confidence)
                weights.append(0.3)  # Layer 1 weight
            
            if layer2_result and layer2_result.ai_analysis_result.confidence > 0:
                confidences.append(layer2_result.ai_analysis_result.confidence)
                weights.append(0.7)  # Layer 2 weight (higher trust in AI)
        
        if not confidences:
            return 0.0
        
        # Calculate weighted harmonic mean
        weighted_sum = sum(w / c for w, c in zip(weights, confidences) if c > 0)
        weight_sum = sum(weights)
        
        if weighted_sum == 0:
            return 0.0
        
        harmonic_mean = weight_sum / weighted_sum
        return min(1.0, harmonic_mean)
    
    def _create_calculation_details(
        self,
        content_scores: Dict[ContentType, float],
        config: ProcessingConfig,
        overall_score: float,
        layer_details: Dict[str, str]
    ) -> str:
        """Create detailed explanation of score calculation"""
        
        details = []
        details.append("=== HARM SCORE CALCULATION ===")
        details.append(f"Final Score: {overall_score:.2f}/100")
        details.append("")
        
        details.append("Content Type Weights:")
        details.append(f"  Text: {config.content_weights.text_weight:.2f}")
        details.append(f"  Image: {config.content_weights.image_weight:.2f}")
        details.append(f"  Audio: {config.content_weights.audio_weight:.2f}")
        details.append("")
        
        details.append("Layer Weights:")
        details.append(f"  Layer 1 (Fast): {config.layer_weights.layer1_weight:.2f}")
        details.append(f"  Layer 2 (AI): {config.layer_weights.layer2_weight:.2f}")
        details.append("")
        
        details.append("Content Scores:")
        for content_type, score in content_scores.items():
            details.append(f"  {content_type.value.title()}: {score:.2f}/100")
            if content_type.value in layer_details:
                details.append(f"    Details: {layer_details[content_type.value]}")
        details.append("")
        
        details.append("Mathematical Formula:")
        details.append("Overall = Σ(Content_Weight × Content_Score)")
        details.append("Content_Score = Layer1_Weight×L1_Score + Layer2_Weight×L2_Score")
        details.append("Layer_Score = Σ(Category_Severity × Confidence) × Amplification")
        
        return "\n".join(details)
    
    def get_category_risk_analysis(self, categories: List[HarmCategory]) -> Dict[str, any]:
        """Provide detailed risk analysis for detected categories"""
        if not categories:
            return {"risk_level": "LOW", "recommendations": []}
        
        # Calculate risk levels
        high_risk_categories = {
            HarmCategory.HATE_SPEECH, HarmCategory.VIOLENCE, 
            HarmCategory.SELF_HARM, HarmCategory.ILLEGAL_ACTIVITY
        }
        
        medium_risk_categories = {
            HarmCategory.SEXUAL_CONTENT, HarmCategory.HARASSMENT,
            HarmCategory.TOXIC_BEHAVIOR
        }
        
        high_risk_found = any(cat in high_risk_categories for cat in categories)
        medium_risk_found = any(cat in medium_risk_categories for cat in categories)
        
        if high_risk_found:
            risk_level = "HIGH"
        elif medium_risk_found:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Generate recommendations
        recommendations = []
        if HarmCategory.VIOLENCE in categories:
            recommendations.append("Immediate review required - violent content detected")
        if HarmCategory.HATE_SPEECH in categories:
            recommendations.append("High priority review - hate speech detected")
        if HarmCategory.SELF_HARM in categories:
            recommendations.append("Urgent: Self-harm content requires immediate intervention")
        if len(categories) >= 3:
            recommendations.append("Multiple violation types - comprehensive review needed")
        
        return {
            "risk_level": risk_level,
            "category_count": len(categories),
            "high_severity_count": len([c for c in categories if c in high_risk_categories]),
            "recommendations": recommendations
        } 