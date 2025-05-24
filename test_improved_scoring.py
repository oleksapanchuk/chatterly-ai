#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.scoring_service import ScoringService
from services.improved_scoring_service import ImprovedScoringService
from shared.content_category import ContentCategory
from shared.gpt_text_analysis_result import GptTextAnalysisResult
from shared.moderation_result import ModerationResult
from shared.validation_types import SeverityLevel

def create_text_result(categories, severities, confidences, is_harmful=True):
    """Helper to create GptTextAnalysisResult for testing."""
    confidence_dict = {}
    for i, category in enumerate(categories):
        confidence_dict[category] = confidences[i] if i < len(confidences) else 0.8
    
    return GptTextAnalysisResult(
        is_harmful=is_harmful,
        categories=categories,
        severity=severities[0] if severities else SeverityLevel.MEDIUM,
        confidence=confidence_dict,
        explanation="Test result"
    )

def create_image_result(category_scores, is_harmful=True):
    """Helper to create ModerationResult for testing."""
    return ModerationResult(
        is_harmful=is_harmful,
        categories=list(category_scores.keys()),
        score=category_scores
    )

def print_comparison(scenario_name, old_score, new_score):
    """Print comparison between old and new scoring systems."""
    difference = new_score - old_score
    percentage_change = ((new_score - old_score) / max(old_score, 1)) * 100
    
    print(f"\n{'='*60}")
    print(f"SCENARIO: {scenario_name}")
    print(f"{'='*60}")
    print(f"Old Score: {old_score:.2f}")
    print(f"New Score: {new_score:.2f}")
    print(f"Difference: {difference:+.2f}")
    print(f"Change: {percentage_change:+.1f}%")
    
    if abs(difference) < 2:
        print("📊 SIMILAR SCORES")
    elif new_score > old_score:
        print("📈 NEW SYSTEM MORE SEVERE")
    else:
        print("📉 NEW SYSTEM LESS SEVERE")

def test_scoring_systems():
    """Test various scenarios with both scoring systems."""
    
    old_scoring = ScoringService()
    new_scoring = ImprovedScoringService()
    
    print("🧪 CONTENT SCORING SYSTEM COMPARISON")
    print("Testing improved probabilistic model vs legacy severity-based model")
    
    # Test Case 1: Single high-severity hate speech
    print("\n" + "="*80)
    print("TEST CASE 1: Single High-Severity Hate Speech")
    print("="*80)
    
    text_results = [create_text_result(
        categories=[ContentCategory.HATE_SPEECH],
        severities=[SeverityLevel.HIGH],
        confidences=[0.9]
    )]
    
    old_score = old_scoring.calculate_content_score(text_results=text_results)
    new_score = new_scoring.calculate_content_score(text_results=text_results)
    print_comparison("High-confidence hate speech", old_score, new_score)
    
    # Test Case 2: Low confidence detection
    print("\n" + "="*80)
    print("TEST CASE 2: Low Confidence Detection")
    print("="*80)
    
    text_results = [create_text_result(
        categories=[ContentCategory.HATE_SPEECH],
        severities=[SeverityLevel.HIGH],
        confidences=[0.3]  # Low confidence
    )]
    
    old_score = old_scoring.calculate_content_score(text_results=text_results)
    new_score = new_scoring.calculate_content_score(text_results=text_results)
    print_comparison("Low-confidence hate speech", old_score, new_score)
    
    # Test Case 3: Multiple categories
    print("\n" + "="*80)
    print("TEST CASE 3: Multiple Categories")
    print("="*80)
    
    text_results = [create_text_result(
        categories=[ContentCategory.HATE_SPEECH, ContentCategory.HARASSMENT, ContentCategory.VIOLENCE],
        severities=[SeverityLevel.MEDIUM],
        confidences=[0.8, 0.7, 0.6]
    )]
    
    old_score = old_scoring.calculate_content_score(text_results=text_results)
    new_score = new_scoring.calculate_content_score(text_results=text_results)
    print_comparison("Multiple category violations", old_score, new_score)
    
    # Test Case 4: Image content
    print("\n" + "="*80)
    print("TEST CASE 4: Image Content")
    print("="*80)
    
    image_results = [create_image_result({
        ContentCategory.VIOLENCE: 0.85,
        ContentCategory.HARASSMENT: 0.60
    })]
    
    old_score = old_scoring.calculate_content_score(image_results=image_results)
    new_score = new_scoring.calculate_content_score(image_results=image_results)
    print_comparison("Violent image content", old_score, new_score)
    
    # Test Case 5: Audio content (transcribed)
    print("\n" + "="*80)
    print("TEST CASE 5: Audio Content (Transcribed)")
    print("="*80)
    
    audio_results = [create_text_result(
        categories=[ContentCategory.SELF_HARM],
        severities=[SeverityLevel.HIGH],
        confidences=[0.7]
    )]
    
    old_score = old_scoring.calculate_content_score(audio_results=audio_results)
    new_score = new_scoring.calculate_content_score(audio_results=audio_results)
    print_comparison("Audio self-harm content", old_score, new_score)
    
    # Test Case 6: Mixed content types
    print("\n" + "="*80)
    print("TEST CASE 6: Mixed Content Types")
    print("="*80)
    
    text_results = [create_text_result(
        categories=[ContentCategory.HATE_SPEECH],
        severities=[SeverityLevel.HIGH],
        confidences=[0.85]
    )]
    
    image_results = [create_image_result({
        ContentCategory.VIOLENCE: 0.75
    })]
    
    audio_results = [create_text_result(
        categories=[ContentCategory.HARASSMENT],
        severities=[SeverityLevel.MEDIUM],
        confidences=[0.60]
    )]
    
    old_score = old_scoring.calculate_content_score(
        text_results=text_results,
        image_results=image_results,
        audio_results=audio_results
    )
    new_score = new_scoring.calculate_content_score(
        text_results=text_results,
        image_results=image_results,
        audio_results=audio_results
    )
    print_comparison("Mixed content types", old_score, new_score)
    
    # Test Case 7: Spam (low-impact content)
    print("\n" + "="*80)
    print("TEST CASE 7: Spam Content")
    print("="*80)
    
    text_results = [create_text_result(
        categories=[ContentCategory.SPAM],
        severities=[SeverityLevel.MEDIUM],
        confidences=[0.9]
    )]
    
    old_score = old_scoring.calculate_content_score(text_results=text_results)
    new_score = new_scoring.calculate_content_score(text_results=text_results)
    print_comparison("High-confidence spam", old_score, new_score)
    
    # Test Case 8: Multiple content items
    print("\n" + "="*80)
    print("TEST CASE 8: Multiple Content Items")
    print("="*80)
    
    text_results = [
        create_text_result([ContentCategory.HATE_SPEECH], [SeverityLevel.HIGH], [0.9]),
        create_text_result([ContentCategory.SPAM], [SeverityLevel.LOW], [0.8]),
        create_text_result([ContentCategory.HARASSMENT], [SeverityLevel.MEDIUM], [0.7])
    ]
    
    old_score = old_scoring.calculate_content_score(text_results=text_results)
    new_score = new_scoring.calculate_content_score(text_results=text_results)
    print_comparison("Multiple text items", old_score, new_score)
    
    # Test Case 9: Edge case - very low confidence
    print("\n" + "="*80)
    print("TEST CASE 9: Very Low Confidence")
    print("="*80)
    
    text_results = [create_text_result(
        categories=[ContentCategory.HATE_SPEECH],
        severities=[SeverityLevel.CRITICAL],
        confidences=[0.1]  # Very low confidence
    )]
    
    old_score = old_scoring.calculate_content_score(text_results=text_results)
    new_score = new_scoring.calculate_content_score(text_results=text_results)
    print_comparison("Very low confidence critical content", old_score, new_score)
    
    # Summary
    print("\n" + "="*80)
    print("🎯 SCORING SYSTEM COMPARISON SUMMARY")
    print("="*80)
    print("✅ Improved system uses probabilistic confidence handling")
    print("✅ Category-specific base risk scores (no arbitrary severity levels)")
    print("✅ Logarithmic multi-category penalties")
    print("✅ Weighted aggregation instead of pure maximum")
    print("✅ Dynamic audio confidence degradation")
    print("✅ Additive content type modifiers (no multiplicative chaos)")
    print("\n📈 Expected benefits:")
    print("   • More consistent scoring across content types")
    print("   • Better handling of low-confidence detections") 
    print("   • Appropriate compounding of multiple violations")
    print("   • Reduced need for artificial score capping")
    print("   • More interpretable risk-based scores")

if __name__ == "__main__":
    test_scoring_systems() 